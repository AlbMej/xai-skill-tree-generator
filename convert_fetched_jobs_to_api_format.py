"""
Convert fetched jobs from xai_jobs.json to API format.
Transforms Greenhouse job data into the required API schema.
"""

import json
import re
import html
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class JobConverter:
    """Converts job data from Greenhouse format to API format."""
    
    def __init__(self):
        self.company_name = "xAI"
        self.company_logo = "https://x.ai/favicon.ico"  # Default xAI logo URL
    
    def clean_html_description(self, description: str) -> str:
        """Clean HTML from job description."""
        if not description:
            return ""
        
        # Decode HTML entities
        text = html.unescape(description)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def extract_salary(self, description: str, salary_range: Optional[str] = None) -> tuple:
        """
        Extract salary information from description or salary_range field.
        Returns: (salary_min, salary_max, currency)
        """
        salary_min = 0
        salary_max = 0
        currency = "USD"
        
        # Try salary_range field first
        if salary_range:
            # Parse formats like "$180,000 - $440,000 USD" or "$45/hour - $100/hour"
            match = re.search(r'\$?([\d,]+)\s*-\s*\$?([\d,]+)\s*(USD|hour|/hour)?', salary_range, re.IGNORECASE)
            if match:
                try:
                    salary_min = int(match.group(1).replace(',', ''))
                    salary_max = int(match.group(2).replace(',', ''))
                    unit = match.group(3) or ""
                    if 'hour' in unit.lower():
                        # Convert hourly to annual (rough estimate: 2080 hours/year)
                        salary_min = salary_min * 2080
                        salary_max = salary_max * 2080
                except ValueError:
                    pass
        
        # Try to extract from description
        if salary_min == 0 and salary_max == 0:
            # Look for salary patterns in description
            patterns = [
                r'\$?([\d,]+)\s*-\s*\$?([\d,]+)\s*(USD|hour|/hour|per year|annually)?',
                r'\$?([\d,]+)\s*(USD|hour|/hour|per year|annually)',
            ]
            
            for pattern in patterns:
                matches = re.finditer(pattern, description, re.IGNORECASE)
                for match in matches:
                    try:
                        if len(match.groups()) >= 2:
                            val1 = int(match.group(1).replace(',', ''))
                            if len(match.groups()) >= 3 and match.group(2):
                                val2 = int(match.group(2).replace(',', ''))
                                salary_min = val1
                                salary_max = val2
                            else:
                                salary_min = val1
                                salary_max = val1
                            
                            unit = match.group(-1) or ""
                            if 'hour' in unit.lower():
                                salary_min = salary_min * 2080
                                salary_max = salary_max * 2080
                            
                            if salary_min > 0:
                                break
                    except (ValueError, IndexError):
                        continue
                
                if salary_min > 0:
                    break
        
        return (salary_min, salary_max, currency)
    
    def extract_location_type(self, location: str, description: str) -> str:
        """
        Extract location type: remote, hybrid, or onsite.
        """
        location_lower = location.lower() if location else ""
        desc_lower = description.lower() if description else ""
        
        combined = f"{location_lower} {desc_lower}"
        
        if 'remote' in combined and ('hybrid' in combined or 'onsite' in combined or 'in-office' in combined):
            return "hybrid"
        elif 'remote' in combined:
            return "remote"
        elif 'onsite' in combined or 'in-office' in combined or 'in office' in combined:
            return "onsite"
        else:
            # Default based on location string
            if 'remote' in location_lower:
                return "remote"
            elif ';' in location or ',' in location:
                # Multiple locations might indicate hybrid
                return "hybrid"
            else:
                return "onsite"
    
    def extract_experience_level(self, description: str, title: str) -> str:
        """
        Extract experience level from description and title.
        Returns: entry, mid, senior, executive, or empty string
        """
        combined = f"{title} {description}".lower()
        
        # Check for senior/lead/principal
        if any(word in combined for word in ['senior', 'sr.', 'lead', 'principal', 'staff', 'architect']):
            return "senior"
        
        # Check for executive/director/manager
        if any(word in combined for word in ['executive', 'director', 'manager', 'head of', 'vp', 'vice president']):
            return "executive"
        
        # Check for entry/junior
        if any(word in combined for word in ['entry', 'junior', 'jr.', 'associate', 'intern', 'internship']):
            return "entry"
        
        # Check for mid-level indicators
        if any(word in combined for word in ['mid-level', 'mid level', '3+ years', '2+ years', '5+ years']):
            return "mid"
        
        return ""  # Unknown
    
    def extract_skills_from_description(self, description: str) -> str:
        """
        Extract skills from job description.
        Returns comma-separated string of skills.
        """
        if not description:
            return ""
        
        # Common technical skills to look for
        tech_skills = [
            'Python', 'JavaScript', 'Java', 'C++', 'C#', 'Go', 'Rust', 'TypeScript', 
            'SQL', 'R', 'Swift', 'Kotlin', 'React', 'Vue', 'Angular', 'Django', 
            'Flask', 'FastAPI', 'Spring', 'Node.js', 'Express', 'TensorFlow', 'PyTorch',
            'Git', 'Docker', 'Kubernetes', 'AWS', 'Azure', 'GCP', 'Linux', 'MongoDB',
            'PostgreSQL', 'Redis', 'Machine Learning', 'AI', 'Deep Learning',
            'CUDA', 'JAX', 'PyTorch', 'TensorFlow'
        ]
        
        found_skills = []
        desc_lower = description.lower()
        
        for skill in tech_skills:
            if skill.lower() in desc_lower:
                found_skills.append(skill)
        
        # Also look for skill patterns in qualifications sections
        qual_patterns = [
            r'(?:required|must have|qualifications?)[^.]*?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:experience with|proficiency in|knowledge of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        for pattern in qual_patterns:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                skill = match.group(1).strip()
                if len(skill) > 2 and skill not in found_skills:
                    # Filter out common false positives
                    if skill not in ['Must', 'Required', 'Have', 'Experience', 'Years']:
                        found_skills.append(skill)
        
        return ", ".join(found_skills[:20])  # Limit to 20 skills
    
    def extract_employment_type(self, description: str) -> str:
        """Extract employment type: full-time, part-time, contract, etc."""
        desc_lower = description.lower() if description else ""
        
        if 'full-time' in desc_lower or 'full time' in desc_lower:
            return "full-time"
        elif 'part-time' in desc_lower or 'part time' in desc_lower:
            return "part-time"
        elif 'contract' in desc_lower:
            return "contract"
        elif 'internship' in desc_lower:
            return "internship"
        else:
            return "full-time"  # Default
    
    def calculate_expires_at(self, updated_at: Optional[str]) -> str:
        """
        Calculate expiration date (e.g., 90 days from update date).
        Returns ISO format string or empty string.
        """
        if not updated_at:
            # Default to 90 days from now
            expires = datetime.now() + timedelta(days=90)
        else:
            try:
                # Parse the updated_at timestamp
                # Format: "2025-11-12T20:57:45-05:00"
                dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                expires = dt + timedelta(days=90)
            except (ValueError, AttributeError):
                expires = datetime.now() + timedelta(days=90)
        
        return expires.isoformat()
    
    def convert_job(self, job: Dict[str, Any], use_skill_tree: bool = False, skill_trees_dir: str = "job_skill_trees") -> Dict[str, Any]:
        """
        Convert a single job from Greenhouse format to API format.
        
        Args:
            job: Job dictionary from xai_jobs.json
            use_skill_tree: Whether to use skill tree data if available
            skill_trees_dir: Directory containing skill tree JSON files
            
        Returns:
            Job in API format
        """
        description = job.get('description', '')
        clean_description = self.clean_html_description(description)
        
        # Extract salary
        salary_min, salary_max, currency = self.extract_salary(
            clean_description, 
            job.get('salary_range')
        )
        
        # Extract location type
        location_type = self.extract_location_type(
            job.get('location', ''),
            clean_description
        )
        
        # Extract experience level
        experience_level = self.extract_experience_level(
            clean_description,
            job.get('title', '')
        )
        
        # Extract skills
        skills_required = self.extract_skills_from_description(clean_description)
        
        # Try to use skill tree data if available
        if use_skill_tree and skills_required == "":
            skills_required = self._extract_skills_from_skill_tree(
                job.get('id'),
                skill_trees_dir
            )
        
        # Extract employment type
        employment_type = self.extract_employment_type(clean_description)
        
        # Calculate expiration
        expires_at = self.calculate_expires_at(job.get('updated_at'))
        
        # Build API format job
        api_job = {
            "company_logo": self.company_logo,
            "company_name": self.company_name,
            "description": clean_description,
            "employment_type": employment_type,
            "experience_level": experience_level,
            "expires_at": expires_at,
            "location": job.get('location', 'Not specified'),
            "location_type": location_type,
            "salary_currency": currency,
            "salary_max": salary_max,
            "salary_min": salary_min,
            "skills_required": skills_required,
            "title": job.get('title', 'Unknown Position')
        }
        
        return api_job
    
    def _extract_skills_from_skill_tree(self, job_id: Optional[int], skill_trees_dir: str) -> str:
        """Extract skills from skill tree JSON file if available."""
        if not job_id:
            return ""
        
        try:
            # Try to find skill tree file
            import os
            import glob
            
            pattern = os.path.join(skill_trees_dir, f"job_{job_id}_*_skill_tree.json")
            files = glob.glob(pattern)
            
            if files:
                with open(files[0], 'r', encoding='utf-8') as f:
                    skill_tree = json.load(f)
                
                # Extract all skill names from the tree
                skills = []
                
                def extract_skills_recursive(node):
                    if isinstance(node, dict):
                        if node.get('type') == 'skill':
                            skills.append(node.get('name', ''))
                        if 'children' in node:
                            for child in node['children']:
                                extract_skills_recursive(child)
                
                extract_skills_recursive(skill_tree)
                return ", ".join(skills[:20])
        except Exception:
            pass
        
        return ""
    
    def convert_all_jobs(self, input_file: str = "xai_jobs.json", output_file: str = "jobs_api_format.json", 
                        use_skill_tree: bool = False, skill_trees_dir: str = "job_skill_trees") -> List[Dict[str, Any]]:
        """
        Convert all jobs from input file to API format.
        
        Args:
            input_file: Path to input JSON file with jobs
            output_file: Path to output JSON file
            use_skill_tree: Whether to use skill tree data for skills
            skill_trees_dir: Directory containing skill tree files
            
        Returns:
            List of converted jobs
        """
        print(f"[*] Loading jobs from {input_file}...")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        jobs = data.get('jobs', [])
        print(f"[*] Found {len(jobs)} jobs to convert")
        
        converted_jobs = []
        
        for i, job in enumerate(jobs, 1):
            try:
                api_job = self.convert_job(job, use_skill_tree, skill_trees_dir)
                converted_jobs.append(api_job)
                
                if i % 50 == 0:
                    print(f"  Converted {i}/{len(jobs)} jobs...")
            except Exception as e:
                print(f"[WARNING] Failed to convert job {job.get('id', 'unknown')}: {e}")
                continue
        
        # Save converted jobs
        print(f"[*] Saving {len(converted_jobs)} converted jobs to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(converted_jobs, f, indent=2, ensure_ascii=False)
        
        print(f"[SUCCESS] Converted {len(converted_jobs)} jobs successfully")
        return converted_jobs


def main():
    """Main entry point."""
    import sys
    
    input_file = "xai_jobs.json"
    output_file = "jobs_api_format.json"
    use_skill_tree = False
    skill_trees_dir = "job_skill_trees"
    
    # Parse command line arguments
    if '--input' in sys.argv:
        idx = sys.argv.index('--input')
        if idx + 1 < len(sys.argv):
            input_file = sys.argv[idx + 1]
    
    if '--output' in sys.argv:
        idx = sys.argv.index('--output')
        if idx + 1 < len(sys.argv):
            output_file = sys.argv[idx + 1]
    
    if '--use-skill-tree' in sys.argv:
        use_skill_tree = True
    
    if '--skill-trees-dir' in sys.argv:
        idx = sys.argv.index('--skill-trees-dir')
        if idx + 1 < len(sys.argv):
            skill_trees_dir = sys.argv[idx + 1]
    
    converter = JobConverter()
    converter.convert_all_jobs(input_file, output_file, use_skill_tree, skill_trees_dir)


if __name__ == "__main__":
    main()

