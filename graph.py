import matplotlib.pyplot as plt
import io
import aiohttp

async def generate_gpu_graph():
    # Fetch the GPU data
    url = "https://app-api.salad.com/api/v2/demand-monitor/gpu"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                gpu_data = await response.json()
            else:
                return None

    # Sort GPUs by average earnings and get top 10
    top_gpus = sorted(gpu_data, key=lambda x: x['earningRates']['avgEarning'], reverse=True)[:10]

    # Prepare data for the graph
    names = [gpu['name'] for gpu in top_gpus]
    earnings = [gpu['earningRates']['avgEarning'] for gpu in top_gpus]

    # Create the graph with adjustments for better fitting of GPU names
    fig, ax = plt.subplots(figsize=(10, 8))  # Increase the figure size to accommodate long names
    ax.barh(names, earnings, color='green')
    ax.set_xlabel('Average Earnings ($)')
    ax.set_title('Top 10 GPUs by Average Earnings')

    # Rotate the labels on the y-axis to prevent cutting off
    plt.yticks(rotation=45, ha='right')  # Rotate labels by 45 degrees and align to the right

    # Save the graph to a BytesIO object (in-memory)
    img_buffer = io.BytesIO()
    plt.tight_layout()  # Automatically adjust subplots to fit into the figure area
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)  # Rewind the buffer for reading

    # Return the image buffer
    return img_buffer
