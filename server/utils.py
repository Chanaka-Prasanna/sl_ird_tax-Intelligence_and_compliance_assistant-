from graph import graph


def save_graph(graph, filename="graph.png"):
    """
    Generate and save a mermaid graph image from a graph object.
    
    Args:
        graph: The graph object with get_graph() method
        filename: The filename to save the image (default: "graph.png")
    """
    png_data = graph.get_graph().draw_mermaid_png()
    with open(filename, "wb") as f:
        f.write(png_data)

save_graph(graph)