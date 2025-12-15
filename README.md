# Anime Trends MCP

A data science project analyzing anime character popularity trends from Danbooru artwork metadata, with an MCP (Model Context Protocol) server that enables interactive exploration of the dataset through LLM conversations.

## Overview

This project explores anime character popularity trends using metadata from Danbooru, one of the largest anime artwork databases. The analysis reveals insights about character lifecycles, trait evolution, and cultural trends in anime fandom. The MCP server exposes these insights as interactive tools that can be accessed through LLM assistants like Claude.

## Dataset

The dataset consists of metadata from the **Danbooru 2024** dataset, containing:
- **Source**: [deepghs/danbooru2024-webp-4Mpixel](https://huggingface.co/datasets/deepghs/danbooru2024-webp-4Mpixel) on Hugging Face
- **Fields Used**: 
  - `created_at`: Timestamp of artwork upload
  - `tag_string`: Space-separated tags describing the artwork (characters, traits, etc.)
- **Time Range**: 2005-2024 (with some data extending into 2025)
- **Size**: Millions of artwork entries

The dataset is downloaded automatically when running `main.ipynb` (requires Hugging Face authentication token).

## Data Science Insights

The `main.ipynb` notebook contains several analyses exploring anime character trends:

### 1. Character Popularity Lifecycles
Tracks how character popularity evolves over time, showing rise and decline patterns. Examples include Rem (Re:Zero), Makima (Chainsaw Man), Frieren, Hatsune Miku, and Lucy (Cyberpunk).

### 2. Trait Popularity Evolution
Analyzes how specific traits (maid outfits, school uniforms, swimsuits, bunny girls, cat ears) have evolved as a percentage of all uploads over time, revealing cultural shifts in anime aesthetics.

### 3. Top Characters by Year
Identifies the top 10 most popular characters for each year (2015-2024), filtering out metadata tags and focusing on actual character entities.

### 4. Character Co-occurrence Analysis
Heatmap visualization showing how often characters appear together in artworks, useful for understanding character relationships and "shipping" patterns.

### 5. Hair Color Trends
Stacked area chart showing the evolution of hair color preferences in anime artwork over time.

### 6. Tag Driver Analysis
Identifies which characters drive the popularity of specific traits (e.g., which characters with black hair were most popular in a given year).

## MCP Server

The MCP server (`server.py`) exposes five interactive tools for exploring the dataset:

### Available Tools

1. **`get_top_waifus_by_year(year: int)`**
   - Returns the top 10 most popular anime characters for a specific year
   - Applies sophisticated filtering to identify true character entities
   - Validates year input (2005-2025)

2. **`get_character_stats(character_tag: str)`**
   - Returns statistics for a character: total artworks, peak popularity date, current status
   - Generates and saves a popularity timeline chart
   - Example: `"rem_(re:zero)"` or `"hatsune_miku"`

3. **`calculate_ship_dependency(char1: str, char2: str)`**
   - Calculates how often two characters appear together in artworks
   - Returns co-occurrence percentage and joint image count
   - Useful for analyzing character relationships

4. **`analyze_tag_driver(year: int, tag: str)`**
   - Identifies the top 5 characters driving a specific tag's popularity in a given year
   - Generates a bar chart visualization
   - Example: Find which characters drove "black_hair" popularity in 2016

5. **`compare_characters(char1: str, char2: str)`**
   - Head-to-head comparison of two characters
   - Shows total artworks and generates a comparison timeline chart
   - Declares a "winner" based on total popularity

### Server Features

- **Input Validation**: Uses Pydantic models to validate inputs and provide helpful error messages
- **Chart Generation**: Automatically generates and saves visualization charts to the `charts/` directory
- **Robust Filtering**: Sophisticated tag filtering to identify real characters vs. metadata tags
- **Error Handling**: Graceful handling of missing data or invalid inputs

## Setup

### Prerequisites

- Python 3.8+
- Hugging Face account and access token (for downloading the dataset)

### Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd anime-trends-mcp
```

2. Install dependencies:
```bash
pip install pandas matplotlib seaborn numpy python-dotenv huggingface-hub fastmcp pydantic
```

3. Set up Hugging Face authentication:
   - Create a `.env` file in the project root
   - Add your Hugging Face token: `HF_TOKEN=your_token_here`
   - Or use `huggingface-cli login`

4. Download the dataset:
   - Run the cells in `main.ipynb` to download `metadata.parquet`
   - Or download manually from Hugging Face

### Running the MCP Server

```bash
python server.py
```

The server will start and be ready to accept MCP connections. Configure your MCP client (e.g., Claude Desktop) to connect to this server.

### MCP Configuration

Add to your MCP client configuration (e.g., Claude Desktop's `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "danbooru-analytics": {
      "command": "python",
      "args": ["/path/to/anime-trends-mcp/server.py"]
    }
  }
}
```

## Project Structure

```
anime-trends-mcp/
├── main.ipynb              # Jupyter notebook with data science analyses
├── server.py                # MCP server implementation
├── metadata.parquet         # Dataset file (downloaded from Hugging Face)
├── charts/                  # Generated visualization charts
│   ├── popularity_*.png
│   ├── compare_*.png
│   └── drivers_*.png
├── README.md                # This file
├── LICENSE                  # License file
└── .gitignore              # Git ignore rules
```

## Usage Examples

### Example 1: Find Top Characters of 2016
```
User: "What were the top 10 most popular anime characters in 2016?"
LLM: [Calls get_top_waifus_by_year(2016)]
```

### Example 2: Analyze Character Popularity
```
User: "Show me the popularity stats for Rem from Re:Zero"
LLM: [Calls get_character_stats("rem_(re:zero)")]
```

### Example 3: Compare Characters
```
User: "Compare Rem and Emilia from Re:Zero"
LLM: [Calls compare_characters("rem_(re:zero)", "emilia_(re:zero)")]
```

### Example 4: Find Tag Drivers
```
User: "What characters drove the popularity of black hair in 2012?"
LLM: [Calls analyze_tag_driver(2012, "black_hair")]
```

### Example 5: Ship Analysis
```
User: "How often do Rem and Ram appear together?"
LLM: [Calls calculate_ship_dependency("rem_(re:zero)", "ram_(re:zero)")]
```

## Technical Details

### Tag Filtering Strategy

The project uses sophisticated filtering to identify real character entities:

- **VIP List**: Known popular characters that don't follow standard naming conventions
- **Bad Suffixes**: Filters out metadata tags like `_(series)`, `_(medium)`, `_(style)`, etc.
- **Specific Bans**: Removes common non-character tags like `star_(symbol)`, `heart`, etc.
- **Pattern Matching**: Looks for tags with parentheses (e.g., `rem_(re:zero)`) which typically indicate character names

### Data Processing

- Timestamps are normalized to UTC
- Monthly/yearly aggregations use pandas resampling
- Charts use matplotlib/seaborn for visualization
- All generated charts are saved to the `charts/` directory


## License

See `LICENSE` file for details.

## Acknowledgments

- Danbooru community for maintaining the artwork database
- Hugging Face for hosting the dataset
- MCP (Model Context Protocol) for enabling LLM integration

## Contact

For questions or issues, please open an issue in the repository.
