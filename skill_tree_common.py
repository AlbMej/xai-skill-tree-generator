"""
Common functionality for skill tree generation.
Shared between resume and job posting skill tree generators.
"""

import json
from typing import Dict, Any


def build_skill_tree(skill_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a hierarchical skill tree structure from skill data.
    
    Args:
        skill_data: Dictionary with skills organized by category
        
    Returns:
        Hierarchical skill tree dictionary
    """
    tree = {
        "name": "Skills",
        "children": []
    }
    
    # Add technical skills
    if "technical" in skill_data.get("skills", {}):
        tech_skills = skill_data["skills"]["technical"]
        tech_node = {
            "name": "Technical Skills",
            "children": []
        }
        
        for category, skills in tech_skills.items():
            if skills:
                category_node = {
                    "name": category.replace("_", " ").title(),
                    "children": [{"name": skill, "type": "skill"} for skill in skills]
                }
                tech_node["children"].append(category_node)
        
        if tech_node["children"]:
            tree["children"].append(tech_node)
    
    # Add soft skills
    if skill_data.get("skills", {}).get("soft_skills"):
        soft_node = {
            "name": "Soft Skills",
            "children": [{"name": skill, "type": "skill"} for skill in skill_data["skills"]["soft_skills"]]
        }
        tree["children"].append(soft_node)
    
    # Add domains
    if skill_data.get("skills", {}).get("domains"):
        domain_node = {
            "name": "Domain Expertise",
            "children": [{"name": domain, "type": "skill"} for domain in skill_data["skills"]["domains"]]
        }
        tree["children"].append(domain_node)
    
    # Add certifications
    if skill_data.get("skills", {}).get("certifications"):
        cert_node = {
            "name": "Certifications",
            "children": [{"name": cert, "type": "certification"} for cert in skill_data["skills"]["certifications"]]
        }
        tree["children"].append(cert_node)
    
    # Add education/qualifications
    if skill_data.get("skills", {}).get("education"):
        edu_node = {
            "name": "Education & Qualifications",
            "children": [{"name": qual, "type": "qualification"} for qual in skill_data["skills"]["education"]]
        }
        tree["children"].append(edu_node)
    
    # Add experience requirements
    if skill_data.get("skills", {}).get("experience_requirements"):
        exp_node = {
            "name": "Experience Requirements",
            "children": [{"name": req, "type": "requirement"} for req in skill_data["skills"]["experience_requirements"]]
        }
        tree["children"].append(exp_node)
    
    return tree


def generate_html_visualization(skill_tree: Dict[str, Any], output_path: str, title: str = "Skill Tree Visualization"):
    """
    Generate an interactive HTML visualization of the skill tree.
    
    Args:
        skill_tree: Hierarchical skill tree dictionary
        output_path: Path to save HTML file
        title: Title for the visualization
    """
    
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 30px;
            font-size: 2.5em;
        }}
        .skill-tree {{
            width: 100%;
            height: 800px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            overflow: auto;
        }}
        .node circle {{
            fill: #fff;
            stroke: #667eea;
            stroke-width: 3px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .node circle:hover {{
            stroke-width: 5px;
            fill: #f0f0ff;
        }}
        .node--internal circle {{
            fill: #764ba2;
            stroke: #667eea;
        }}
        .node--leaf circle {{
            fill: #4CAF50;
            stroke: #45a049;
        }}
        .node--certification circle {{
            fill: #FF9800;
            stroke: #F57C00;
        }}
        .node--qualification circle {{
            fill: #2196F3;
            stroke: #1976D2;
        }}
        .node--requirement circle {{
            fill: #F44336;
            stroke: #D32F2F;
        }}
        .node text {{
            font: 14px sans-serif;
            font-weight: 500;
            pointer-events: none;
        }}
        .link {{
            fill: none;
            stroke: #ccc;
            stroke-width: 2px;
        }}
        .tooltip {{
            position: absolute;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            pointer-events: none;
            font-size: 12px;
            opacity: 0;
            transition: opacity 0.3s;
        }}
        .controls {{
            margin-bottom: 20px;
            text-align: center;
        }}
        button {{
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 5px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }}
        button:hover {{
            background: #5568d3;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        <div class="controls">
            <button onclick="zoomIn()">Zoom In</button>
            <button onclick="zoomOut()">Zoom Out</button>
            <button onclick="resetZoom()">Reset</button>
            <button onclick="expandAll()">Expand All</button>
            <button onclick="collapseAll()">Collapse All</button>
        </div>
        <div class="skill-tree" id="skill-tree"></div>
    </div>
    <div class="tooltip" id="tooltip"></div>

    <script>
        const skillTreeData = SKILL_TREE_DATA;
        
        let svg, g, zoom, root, tooltip;
        let currentTransform = d3.zoomIdentity;
        
        function init() {{
            tooltip = d3.select("#tooltip");
            
            svg = d3.select("#skill-tree")
                .append("svg")
                .attr("width", "100%")
                .attr("height", "100%");
            
            g = svg.append("g");
            
            zoom = d3.zoom()
                .scaleExtent([0.1, 3])
                .on("zoom", (event) => {{
                    currentTransform = event.transform;
                    g.attr("transform", event.transform);
                }});
            
            svg.call(zoom);
            
            root = d3.hierarchy(skillTreeData);
            root.x0 = 0;
            root.y0 = 0;
            root.descendants().forEach((d, i) => {{
                d.id = i;
                d._children = d.children;
                if (d.depth > 2) d.children = null;
            }});
            
            update(root);
        }}
        
        function update(source) {{
            const treeLayout = d3.tree().size([800, 1000]);
            treeLayout(root);
            
            const nodes = root.descendants();
            const links = root.links();
            
            const node = g.selectAll("g.node")
                .data(nodes, d => d.id);
            
            const nodeEnter = node.enter()
                .append("g")
                .attr("class", d => {{
                    if (d.children) return "node node--internal";
                    if (d.data.type === "certification") return "node node--certification";
                    if (d.data.type === "qualification") return "node node--qualification";
                    if (d.data.type === "requirement") return "node node--requirement";
                    return "node node--leaf";
                }})
                .attr("transform", d => `translate(${{source.y0}},${{source.x0}})`)
                .on("click", (event, d) => {{
                    if (d.children) {{
                        d._children = d.children;
                        d.children = null;
                    }} else {{
                        d.children = d._children;
                    }}
                    update(d);
                }})
                .on("mouseover", (event, d) => {{
                    tooltip
                        .style("opacity", 1)
                        .html(`<strong>${{d.data.name}}</strong><br/>${{d.depth > 0 ? "Click to expand/collapse" : ""}}`)
                        .style("left", (event.pageX + 10) + "px")
                        .style("top", (event.pageY - 10) + "px");
                }})
                .on("mouseout", () => {{
                    tooltip.style("opacity", 0);
                }});
            
            nodeEnter.append("circle")
                .attr("r", d => d.depth === 0 ? 15 : d.depth === 1 ? 12 : 8)
                .style("fill", d => {{
                    if (d.depth === 0) return "#667eea";
                    if (d.data.type === "certification") return "#FF9800";
                    if (d.data.type === "qualification") return "#2196F3";
                    if (d.data.type === "requirement") return "#F44336";
                    return d.children ? "#764ba2" : "#4CAF50";
                }});
            
            nodeEnter.append("text")
                .attr("dy", ".35em")
                .attr("x", d => d.children || d._children ? -13 : 13)
                .style("text-anchor", d => d.children || d._children ? "end" : "start")
                .text(d => d.data.name)
                .style("font-size", d => d.depth === 0 ? "16px" : d.depth === 1 ? "14px" : "12px");
            
            const nodeUpdate = nodeEnter.merge(node);
            
            nodeUpdate.transition()
                .duration(300)
                .attr("transform", d => `translate(${{d.y}},${{d.x}})`);
            
            nodeUpdate.select("circle")
                .attr("r", d => d.depth === 0 ? 15 : d.depth === 1 ? 12 : 8);
            
            const nodeExit = node.exit()
                .transition()
                .duration(300)
                .attr("transform", d => `translate(${{source.y}},${{source.x}})`)
                .remove();
            
            const link = g.selectAll("path.link")
                .data(links, d => d.target.id);
            
            const linkEnter = link.enter()
                .insert("path", "g")
                .attr("class", "link")
                .attr("d", d => {{
                    const o = {{x: source.x0, y: source.y0}};
                    return diagonal(o, o);
                }});
            
            linkEnter.merge(link)
                .transition()
                .duration(300)
                .attr("d", d => diagonal(d.source, d.target));
            
            link.exit()
                .transition()
                .duration(300)
                .attr("d", d => {{
                    const o = {{x: source.x, y: source.y}};
                    return diagonal(o, o);
                }})
                .remove();
            
            nodes.forEach(d => {{
                d.x0 = d.x;
                d.y0 = d.y;
            }});
        }}
        
        function diagonal(s, d) {{
            return `M ${{s.y}} ${{s.x}}
                    C ${{(s.y + d.y) / 2}} ${{s.x}},
                      ${{(s.y + d.y) / 2}} ${{d.x}},
                      ${{d.y}} ${{d.x}}`;
        }}
        
        function zoomIn() {{
            svg.transition().call(zoom.scaleBy, 1.5);
        }}
        
        function zoomOut() {{
            svg.transition().call(zoom.scaleBy, 0.67);
        }}
        
        function resetZoom() {{
            svg.transition().call(zoom.transform, d3.zoomIdentity);
        }}
        
        function expandAll() {{
            root.descendants().forEach(d => {{
                if (d._children) {{
                    d.children = d._children;
                    d._children = null;
                }}
            }});
            update(root);
        }}
        
        function collapseAll() {{
            root.descendants().forEach(d => {{
                if (d.children && d.depth > 1) {{
                    d._children = d.children;
                    d.children = null;
                }}
            }});
            update(root);
        }}
        
        init();
    </script>
</body>
</html>"""
    
    # Inject the skill tree data into the HTML
    skill_tree_json = json.dumps(skill_tree, indent=2)
    html_content = html_template.replace('SKILL_TREE_DATA', skill_tree_json)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

