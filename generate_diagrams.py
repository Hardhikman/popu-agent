import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.lines import Line2D
import os

def create_policy_analysis_architecture():
    """Create policy analysis architecture diagram"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 8))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    # Add title
    ax.text(7, 7.5, 'Policy Analysis Architecture', fontsize=18, fontweight='bold', ha='center')
    
    # Define positions for components
    positions = {
        'User Input': (1, 6),
        'Policy Analyst': (4, 6),
        'Policy Critic': (7, 6),
        'Policy Lobbyist': (10, 6),
        'Policy Synthesizer': (7, 4),
        'Final Report': (7, 2),
        'Tavily Search': (7, 1)
    }
    
    # Draw components
    components = {
        'User Input': {'color': 'lightblue', 'text': 'User Input\nPolicy Topic'},
        'Policy Analyst': {'color': 'lightgreen', 'text': 'Policy Analyst\nAgent'},
        'Policy Critic': {'color': 'lightgreen', 'text': 'Policy Critic\nAgent'},
        'Policy Lobbyist': {'color': 'lightgreen', 'text': 'Policy Lobbyist\nAgent'},
        'Policy Synthesizer': {'color': 'lightgreen', 'text': 'Policy Synthesizer\nAgent'},
        'Final Report': {'color': 'lightyellow', 'text': 'Final Policy\nReport'},
        'Tavily Search': {'color': 'lightcoral', 'text': 'Tavily Search\nTool/API'}
    }
    
    # Draw rectangles for components
    for name, pos in positions.items():
        x, y = pos
        component = components[name]
        
        # Draw rectangle
        rect = patches.Rectangle((x-1.2, y-0.5), 2.4, 1, linewidth=2, 
                                edgecolor='black', facecolor=component['color'])
        ax.add_patch(rect)
        
        # Add text
        ax.text(x, y, component['text'], ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Draw arrows (workflow)
    arrow_props = dict(arrowstyle='->', lw=2, color='black')
    
    # Main workflow arrows
    ax.annotate('', xy=(4-1.2, 6), xytext=(1+1.2, 6), arrowprops=arrow_props)
    ax.annotate('', xy=(7-1.2, 6), xytext=(4+1.2, 6), arrowprops=arrow_props)
    ax.annotate('', xy=(10-1.2, 6), xytext=(7+1.2, 6), arrowprops=arrow_props)
    
    # Connect Synthesizer from all three agents
    ax.annotate('', xy=(7, 4+0.5), xytext=(4, 6-0.5), arrowprops=arrow_props)
    ax.annotate('', xy=(7, 4+0.5), xytext=(7, 6-0.5), arrowprops=arrow_props)
    ax.annotate('', xy=(7, 4+0.5), xytext=(10, 6-0.5), arrowprops=arrow_props)
    
    # Final report
    ax.annotate('', xy=(7, 2+0.5), xytext=(7, 4-0.5), arrowprops=arrow_props)
    
    # Tool usage arrows (dashed)
    dashed_arrow_props = dict(arrowstyle='->', lw=1.5, color='gray', linestyle='--')
    ax.annotate('', xy=(7, 1+0.5), xytext=(4, 6-0.5), arrowprops=dashed_arrow_props)
    ax.annotate('', xy=(7, 1+0.5), xytext=(7, 6-0.5), arrowprops=dashed_arrow_props)
    ax.annotate('', xy=(7, 1+0.5), xytext=(10, 6-0.5), arrowprops=dashed_arrow_props)
    
    # Add legend
    legend_elements = [
        Line2D([0], [0], color='black', lw=2, label='Agent Workflow'),
        Line2D([0], [0], color='gray', lw=1.5, linestyle='--', label='Tool Usage')
    ]
    ax.legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(0.98, 0.98), fontsize=12)
    
    # Save the figure
    plt.tight_layout()
    plt.savefig('policy_analysis_architecture.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_system_architecture():
    """Create system architecture diagram"""
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Add title
    ax.text(7, 9.5, 'System Architecture', fontsize=16, fontweight='bold', ha='center')
    
    # Define positions for components
    positions = {
        'UI': (2, 8),
        'Main App': (2, 6),
        'Analyst': (5, 7),
        'Critic': (5, 5),
        'Lobbyist': (8, 7),
        'Synthesizer': (8, 5),
        'Tavily Tool': (11, 7),
        'Tavily API': (11, 5),
        'Gemini': (11, 3),
        'Download': (2, 4)  # New component for download functionality
    }
    
    # Draw components grouped by layers
    # Frontend
    frontend_rect = patches.Rectangle((0.5, 7.5), 3, 2, linewidth=1, 
                                     edgecolor='blue', facecolor='lightblue', alpha=0.3)
    ax.add_patch(frontend_rect)
    ax.text(2, 9.2, 'Frontend', fontsize=12, fontweight='bold', ha='center')
    
    # Backend
    backend_rect = patches.Rectangle((4, 4), 5, 4, linewidth=1, 
                                   edgecolor='green', facecolor='lightgreen', alpha=0.3)
    ax.add_patch(backend_rect)
    ax.text(6.5, 8.2, 'Backend', fontsize=12, fontweight='bold', ha='center')
    
    # External Services
    external_rect = patches.Rectangle((10, 2), 3, 6, linewidth=1, 
                                    edgecolor='red', facecolor='lightcoral', alpha=0.3)
    ax.add_patch(external_rect)
    ax.text(11.5, 8.2, 'External Services', fontsize=12, fontweight='bold', ha='center')
    
    # Component details
    components = {
        'UI': {'color': 'white', 'text': 'User Interface\nGradio Web App'},
        'Main App': {'color': 'white', 'text': 'Main Application\nOrchestrator'},
        'Analyst': {'color': 'white', 'text': 'Policy Analyst\nAgent'},
        'Critic': {'color': 'white', 'text': 'Policy Critic\nAgent'},
        'Lobbyist': {'color': 'white', 'text': 'Policy Lobbyist\nAgent'},
        'Synthesizer': {'color': 'white', 'text': 'Policy Synthesizer\nAgent'},
        'Tavily Tool': {'color': 'white', 'text': 'Tavily Search\nTool'},
        'Tavily API': {'color': 'white', 'text': 'Tavily API'},
        'Gemini': {'color': 'white', 'text': 'Gemini Model'},
        'Download': {'color': 'white', 'text': 'Download Report\nFunction'}  # New component
    }
    
    # Draw rectangles for components
    for name, pos in positions.items():
        x, y = pos
        component = components[name]
        
        # Draw rectangle
        rect = patches.Rectangle((x-1, y-0.5), 2, 1, linewidth=1, 
                                edgecolor='black', facecolor=component['color'])
        ax.add_patch(rect)
        
        # Add text
        ax.text(x, y, component['text'], ha='center', va='center', fontsize=8)
    
    # Draw connections
    arrow_props = dict(arrowstyle='->', lw=1, color='black')
    
    # UI to Main App
    ax.annotate('', xy=(2, 6+0.5), xytext=(2, 8-0.5), arrowprops=arrow_props)
    
    # Main App to Agents
    ax.annotate('', xy=(5-1, 7), xytext=(2+1, 6), arrowprops=arrow_props)
    ax.annotate('', xy=(5-1, 5), xytext=(2+1, 6), arrowprops=arrow_props)
    
    # Connect Lobbyist from both Analyst and Critic
    ax.annotate('', xy=(8-1, 7), xytext=(5+1, 7), arrowprops=arrow_props)  # Analyst to Lobbyist
    ax.annotate('', xy=(8-1, 7), xytext=(5+1, 5), arrowprops=arrow_props)  # Critic to Lobbyist
    
    # Connect Synthesizer from all agents
    ax.annotate('', xy=(8-1, 5), xytext=(5+1, 7), arrowprops=arrow_props)  # Analyst to Synthesizer
    ax.annotate('', xy=(8-1, 5), xytext=(5+1, 5), arrowprops=arrow_props)  # Critic to Synthesizer
    ax.annotate('', xy=(8-1, 5), xytext=(8+1, 7), arrowprops=arrow_props)  # Lobbyist to Synthesizer
    
    # Agents to Tools
    ax.annotate('', xy=(11-1, 7), xytext=(5+1, 7), arrowprops=arrow_props)
    ax.annotate('', xy=(11-1, 7), xytext=(5+1, 5), arrowprops=arrow_props)
    ax.annotate('', xy=(11-1, 7), xytext=(8+1, 7), arrowprops=arrow_props)
    ax.annotate('', xy=(11-1, 7), xytext=(8+1, 5), arrowprops=arrow_props)
    
    # Tools to APIs
    ax.annotate('', xy=(11, 5+0.5), xytext=(11, 7-0.5), arrowprops=arrow_props)
    ax.annotate('', xy=(11, 3+0.5), xytext=(2, 6-0.5), arrowprops=arrow_props)
    
    # Main App to Download function
    ax.annotate('', xy=(2-1, 4), xytext=(2+1, 6), arrowprops=arrow_props)
    
    # UI to Download button
    ax.annotate('', xy=(2, 4+0.5), xytext=(2, 8-0.5), arrowprops=arrow_props)
    
    # Save the figure
    plt.tight_layout()
    plt.savefig('system_architecture.png', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    create_policy_analysis_architecture()
    create_system_architecture()
    print("Architecture diagrams generated successfully!")