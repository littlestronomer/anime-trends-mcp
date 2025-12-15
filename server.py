from mcp.server.fastmcp import FastMCP
import pandas as pd
from collections import Counter
import os
import matplotlib
# Set backend to 'Agg' to prevent server from trying to open a window
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from pydantic import BaseModel, Field, ValidationError

# 1. Initialize Server
mcp = FastMCP("Danbooru-Analytics")

# 2. Load Data (Global State)
base_dir = os.path.dirname(os.path.abspath(__file__))
parquet_path = os.path.join(base_dir, "metadata.parquet")
charts_dir = os.path.join(base_dir, "charts")

# Create charts directory if it doesn't exist
os.makedirs(charts_dir, exist_ok=True)

try:
    df = pd.read_parquet(parquet_path, columns=["created_at", "tag_string"])
    df['created_at'] = pd.to_datetime(df['created_at'], utc=True)
except Exception as e:
    df = pd.DataFrame()

# --- CONFIGURATION ---
SPECIFIC_BANS = {
    'star_(symbol)', 'star_(sky)', 'pom_pom_(clothes)', 'shrug_(clothing)',
    'poke_ball_(basic)', 'vision_(genshin_impact)', 'sensei_(blue_archive)',
    'idolmaster_(classic)', 'mahou_shoujo_madoka_magica_(anime)',
    'admiral_(kancolle)', 'producer_(idolmaster)', 'commander_(azur_lane)',
    'doctor_(arknights)', 'traveler_(genshin_impact)', 'trainer_(pokemon)',
    'summoner_(fire_emblem)', 'gudako_(fate/grand_order)', 'unknown_(series)',
    'check_commentary_(request)', 'translation_(request)', 'original_(character)',
    'spot_the_difference', 'comic', 'monochrome', 'heart', 'exclamation_point'
}

BAD_SUFFIXES = (
    '_(series)', '_(medium)', '_(style)', '_(source)',
    '_(cosplay)', '_(object)', '_(group)', '_(production)',
    '_(creature)', '_(game)', '_(request)', '_(event)',
    '_(art_style)', '_(artist)', '_(lore)', '_(meta)',
    '_(costume)', '_(parody)'
)

VIPS = {
    'hatsune_miku', 'hakurei_reimu', 'kirisame_marisa',
    'remilia_scarlet', 'flandre_scarlet', 'kochiya_sanae',
    'izayoi_sakuya', 'konpaku_youmu', 'cirno', 'kagamine_rin'
}


# --- PYDANTIC MODELS ---

class YearInput(BaseModel):
    """
    Validates that the input year is within the dataset's range.
    """
    year: int = Field(..., ge=2005, le=2025, description="Year to analyze (2005-2025)")


class TagInput(BaseModel):
    """
    Validates a Danbooru tag input.
    """
    tag: str = Field(..., min_length=2, description="The Danbooru tag to analyze (e.g., 'rem_(re:zero)')")


class CompareInput(BaseModel):
    """
    Validates input for comparing two characters.
    """
    char1: str = Field(..., min_length=2, description="First character tag")
    char2: str = Field(..., min_length=2, description="Second character tag")


# --- HELPER FUNCTIONS ---

def get_safe_filename(query_str: str, prefix: str) -> str:
    """
    Sanitizes tag names for filenames to prevent filesystem errors.

    Args:
        query_str (str): The raw tag name (e.g., 'rem_(re:zero)').
        prefix (str): A prefix for the file (e.g., 'popularity').

    Returns:
        str: An absolute path to the safe filename.
    """
    safe_tag = query_str.replace(':', '_').replace('/', '_').replace(' ', '_')
    return os.path.join(charts_dir, f"{prefix}_{safe_tag}.png")


# --- TOOLS ---

@mcp.tool()
def get_top_waifus_by_year(year: int):
    """
    Identifies the Top 10 most popular Anime Characters for a specific year.

    This tool applies complex filtering to remove 'junk' tags, metadata suffixes,
    and generic terms to find true character entities.

    Args:
        year (int): The year to analyze (e.g., 2016).

    Returns:
        str: A formatted list of the top 10 characters or an error message.
    """
    if df.empty: return "Error: Dataset not loaded."

    # Validate Input using Pydantic
    try:
        YearInput(year=year)
    except ValidationError as e:
        return f"Input Error: {e}"

    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    mask = (
            (df['created_at'] >= start_date) &
            (df['created_at'] <= end_date) &
            (df['tag_string'].str.contains('1girl', regex=False, na=False))
    )
    subset = df.loc[mask]

    if subset.empty:
        return f"No data found for {year}."

    all_tags = " ".join(subset['tag_string'].dropna()).split()
    counts = Counter(all_tags)

    top_chars = []

    # Deep scan of top 5000 to find valid characters
    for tag, count in counts.most_common(5000):
        if tag in SPECIFIC_BANS: continue
        is_vip = tag in VIPS
        has_parens = '_(' in tag and tag.endswith(')')

        if is_vip or has_parens:
            if not tag.endswith(BAD_SUFFIXES):
                top_chars.append(tag)
        if len(top_chars) == 10: break

    clean_names = [t.replace('_', ' ').title().replace('(', '[').replace(')', ']') for t in top_chars]

    return f"🏆 Top 10 Waifus of {year}:\n" + "\n".join([f"{i + 1}. {n}" for i, n in enumerate(clean_names)])


@mcp.tool()
def get_character_stats(character_tag: str):
    """
    Returns stats AND saves a popularity graph for the character.

    Args:
        character_tag (str): The exact Danbooru tag (e.g., 'hatsune_miku').

    Returns:
        str: A summary of total artworks, peak popularity, and the path to the saved graph.
    """
    if df.empty: return "Error: Dataset not loaded."

    mask = df['tag_string'].str.contains(character_tag, regex=False, na=False)
    subset = df.loc[mask]

    if subset.empty:
        return f"No data found for tag: {character_tag}. Check spelling on Danbooru."

    # 1. Stats
    total = len(subset)
    monthly = subset.set_index('created_at').resample('ME').size()
    peak_date = monthly.idxmax()
    peak_count = monthly.max()

    # 2. Generate Plot
    plt.figure(figsize=(10, 5))
    plt.plot(monthly.index, monthly.values, color='#ff7f50', linewidth=2)
    plt.title(f"Popularity History: {character_tag}")
    plt.xlabel("Year")
    plt.ylabel("Uploads per Month")
    plt.grid(True, alpha=0.3)

    # 3. Save Figure
    save_path = get_safe_filename(character_tag, "popularity")
    plt.savefig(save_path)
    plt.close()

    status = 'Still Active' if monthly.iloc[-1] > 20 else 'Declining'

    return f"""
    📊 Stats for '{character_tag}':
    - Total Artworks: {total:,}
    - Peak Popularity: {peak_date.strftime('%B %Y')} ({peak_count} uploads/month)
    - Current Status: {status}

    🖼️ **Graph Saved:** {save_path}
    """


@mcp.tool()
def calculate_ship_dependency(char1: str, char2: str):
    """
    Calculates the 'Ship Dependency': How often does Char1 appear with Char2?

    Args:
        char1 (str): The base character tag.
        char2 (str): The potential partner tag.

    Returns:
        str: A statistical summary of their co-occurrence.
    """
    if df.empty: return "Error: Dataset not loaded."

    mask1 = df['tag_string'].str.contains(char1, regex=False, na=False)
    set1 = set(df.loc[mask1].index)
    if not set1: return f"Character {char1} not found."

    mask2 = df['tag_string'].str.contains(char2, regex=False, na=False)
    set2 = set(df.loc[mask2].index)

    intersection = len(set1.intersection(set2))
    percentage = (intersection / len(set1)) * 100

    return f"""
    ❤️ Ship Analysis:
    - When {char1} is drawn, {char2} appears {percentage:.1f}% of the time.
    - {char1} Total Images: {len(set1)}
    - Joint Images: {intersection}
    """


@mcp.tool()
def analyze_tag_driver(year: int, tag: str):
    """
    Identifies drivers for a trend and saves a bar chart.

    Args:
        year (int): The year to investigate.
        tag (str): The trait/tag to analyze (e.g., 'black_hair').

    Returns:
        str: A list of the top 5 characters driving the tag's popularity and a saved chart path.
    """
    if df.empty: return "Error: Dataset not loaded."

    # Validate Input using Pydantic logic
    try:
        YearInput(year=year)
    except ValidationError:
        return "Error: Year must be between 2005 and 2025."

    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    mask = (
            (df['created_at'] >= start_date) &
            (df['created_at'] <= end_date) &
            (df['tag_string'].str.contains(tag, regex=False, na=False))
    )
    subset = df.loc[mask]

    if subset.empty: return f"No data found for tag '{tag}' in {year}."

    all_tags = " ".join(subset['tag_string'].dropna()).split()
    counts = Counter(all_tags)

    top_drivers = []
    plot_labels = []
    plot_values = []

    for t, count in counts.most_common(2000):
        if t == tag or t in SPECIFIC_BANS: continue
        is_vip = t in VIPS
        has_parens = '_(' in t and t.endswith(')')

        if is_vip or has_parens:
            if not t.endswith(BAD_SUFFIXES):
                fmt_name = t.replace('_', ' ').title().replace('(', '').replace(')', '')
                top_drivers.append(f"{t} ({count})")
                plot_labels.append(fmt_name)
                plot_values.append(count)
        if len(top_drivers) == 5: break

    # Generate Plot
    plt.figure(figsize=(10, 6))
    sns.barplot(x=plot_values, y=plot_labels, palette="viridis")
    plt.title(f"Top Characters Driving '{tag}' in {year}")
    plt.xlabel("Number of Co-occurrences")

    save_path = get_safe_filename(f"{year}_{tag}", "drivers")
    plt.savefig(save_path, bbox_inches='tight')
    plt.close()

    clean_drivers = [d.replace('_', ' ').title().replace('(', '[').replace(')', ']') for d in top_drivers]

    return f"""
    🕵️ Analysis of '{tag}' in {year}:
    - Total Images: {len(subset)}
    - Top Drivers: {', '.join(clean_drivers)}

    🖼️ **Graph Saved:** {save_path}
    """


@mcp.tool()
def compare_characters(char1: str, char2: str):
    """
    Compares two characters and saves a comparison chart.

    Args:
        char1 (str): First character tag.
        char2 (str): Second character tag.

    Returns:
        str: Head-to-head stats and a saved comparison chart.
    """
    if df.empty: return "Error: Dataset not loaded."

    def get_stats(tag):
        mask = df['tag_string'].str.contains(tag, regex=False, na=False)
        subset = df.loc[mask]
        if subset.empty: return None, None
        return len(subset), subset.set_index('created_at').resample('ME').size()

    total1, yearly1 = get_stats(char1)
    total2, yearly2 = get_stats(char2)

    if total1 is None: return f"❌ {char1} not found"
    if total2 is None: return f"❌ {char2} not found"

    # Plot Comparison
    plt.figure(figsize=(10, 6))
    # Resample to Year-End for cleaner comparison lines
    y1_plot = yearly1.resample('YE').sum()
    y2_plot = yearly2.resample('YE').sum()

    plt.plot(y1_plot.index, y1_plot.values, label=char1, linewidth=2)
    plt.plot(y2_plot.index, y2_plot.values, label=char2, linewidth=2, linestyle='--')
    plt.legend()
    plt.title(f"Head-to-Head: {char1} vs {char2}")
    plt.grid(True, alpha=0.3)

    save_path = get_safe_filename(f"{char1}_vs_{char2}", "compare")
    plt.savefig(save_path)
    plt.close()

    winner = char1 if total1 > total2 else char2

    return f"""
    ⚔️ **{char1} vs {char2}**
    - {char1}: {total1:,}
    - {char2}: {total2:,}
    - Winner: {winner}

    🖼️ **Comparison Chart Saved:** {save_path}
    """


if __name__ == "__main__":
    mcp.run()