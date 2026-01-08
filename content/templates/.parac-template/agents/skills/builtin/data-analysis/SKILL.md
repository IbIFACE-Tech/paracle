---
name: data-analysis
description: Analyze and interpret data to generate meaningful insights using statistical methods and visualization. Use when working with datasets, metrics, statistics, or when insights from data are needed.
license: Apache-2.0
compatibility: Best with pandas, numpy, matplotlib. Requires file_system and code_executor tools.
metadata:
  author: paracle
  version: "1.0.0"
  category: analysis
  level: advanced
  display_name: "Data Analysis"
  tags:
    - analytics
    - statistics
    - insights
    - data
    - intelligence
  capabilities:
    - statistical_analysis
    - pattern_recognition
    - data_visualization
    - insight_generation
    - correlation_analysis
  requirements:
    - skill_name: question-answering
      min_level: basic
allowed-tools: Read Write Bash(python:*) Bash(pandas:*) Bash(numpy:*)
---

# Data Analysis Skill

## When to use this skill

Use this skill when:
- Analyzing datasets (CSV, JSON, Excel, databases)
- Calculating statistics (mean, median, mode, standard deviation)
- Identifying patterns and trends
- Detecting anomalies or outliers
- Generating insights from data
- Creating visualizations
- Comparing groups or segments
- Performing correlation analysis

## Core capabilities

### 1. Descriptive Statistics

Calculate summary statistics to understand data distribution:

```python
import pandas as pd
import numpy as np

def analyze_dataset(data: pd.DataFrame) -> dict:
    """Generate comprehensive statistical summary.

    Args:
        data: DataFrame to analyze

    Returns:
        Dictionary with statistical metrics
    """
    stats = {
        'shape': data.shape,
        'columns': list(data.columns),
        'dtypes': data.dtypes.to_dict(),
        'missing_values': data.isnull().sum().to_dict(),
        'numeric_summary': {},
        'categorical_summary': {}
    }

    # Numeric columns analysis
    numeric_cols = data.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        stats['numeric_summary'][col] = {
            'mean': data[col].mean(),
            'median': data[col].median(),
            'std': data[col].std(),
            'min': data[col].min(),
            'max': data[col].max(),
            'q25': data[col].quantile(0.25),
            'q75': data[col].quantile(0.75),
        }

    # Categorical columns analysis
    categorical_cols = data.select_dtypes(include=['object', 'category']).columns
    for col in categorical_cols:
        stats['categorical_summary'][col] = {
            'unique_values': data[col].nunique(),
            'most_common': data[col].mode().iloc[0] if len(data[col].mode()) > 0 else None,
            'distribution': data[col].value_counts().head(5).to_dict()
        }

    return stats

# Usage
df = pd.read_csv('sales_data.csv')
stats = analyze_dataset(df)
print(f"Dataset shape: {stats['shape']}")
print(f"Missing values: {stats['missing_values']}")
```

### 2. Pattern Recognition

Identify trends and patterns in time series or sequential data:

```python
def detect_trend(data: pd.Series) -> dict:
    """Detect trend direction and strength.

    Args:
        data: Time series data

    Returns:
        Dict with trend direction, slope, and R²
    """
    from scipy import stats as sp_stats

    x = np.arange(len(data))
    y = data.values

    # Remove NaN values
    mask = ~np.isnan(y)
    x_clean = x[mask]
    y_clean = y[mask]

    if len(x_clean) < 2:
        return {'trend': 'insufficient_data'}

    # Linear regression
    slope, intercept, r_value, p_value, std_err = sp_stats.linregress(x_clean, y_clean)

    trend = {
        'direction': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'flat',
        'slope': slope,
        'r_squared': r_value ** 2,
        'p_value': p_value,
        'significant': p_value < 0.05
    }

    return trend

# Usage
monthly_sales = pd.Series([100, 120, 115, 135, 150, 145, 170, 180])
trend = detect_trend(monthly_sales)
print(f"Trend: {trend['direction']} (R²={trend['r_squared']:.3f})")
```

### 3. Anomaly Detection

Find outliers and unusual data points:

```python
def detect_outliers(data: pd.Series, method: str = 'iqr') -> pd.Series:
    """Detect outliers using IQR or Z-score method.

    Args:
        data: Data series to check
        method: 'iqr' (Interquartile Range) or 'zscore'

    Returns:
        Boolean series marking outliers as True
    """
    if method == 'iqr':
        q1 = data.quantile(0.25)
        q3 = data.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers = (data < lower_bound) | (data > upper_bound)

    elif method == 'zscore':
        z_scores = np.abs((data - data.mean()) / data.std())
        outliers = z_scores > 3

    else:
        raise ValueError(f"Unknown method: {method}")

    return outliers

# Usage
prices = pd.Series([100, 105, 102, 110, 500, 108, 103, 107])  # 500 is outlier
outliers = detect_outliers(prices)
print(f"Outliers detected: {prices[outliers].tolist()}")
```

### 4. Correlation Analysis

Understand relationships between variables:

```python
def analyze_correlations(data: pd.DataFrame, threshold: float = 0.5) -> dict:
    """Find strong correlations between numeric columns.

    Args:
        data: DataFrame with numeric columns
        threshold: Minimum absolute correlation value

    Returns:
        Dict with correlation matrix and strong correlations
    """
    # Compute correlation matrix
    corr_matrix = data.select_dtypes(include=[np.number]).corr()

    # Find strong correlations
    strong_correlations = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            col1 = corr_matrix.columns[i]
            col2 = corr_matrix.columns[j]
            corr_value = corr_matrix.iloc[i, j]

            if abs(corr_value) >= threshold:
                strong_correlations.append({
                    'var1': col1,
                    'var2': col2,
                    'correlation': corr_value,
                    'strength': 'strong' if abs(corr_value) > 0.7 else 'moderate'
                })

    return {
        'correlation_matrix': corr_matrix,
        'strong_correlations': strong_correlations
    }

# Usage
df = pd.DataFrame({
    'sales': [100, 150, 200, 250, 300],
    'marketing_spend': [10, 15, 25, 30, 40],
    'temperature': [20, 22, 19, 21, 23]
})
result = analyze_correlations(df, threshold=0.5)
print(f"Strong correlations found: {len(result['strong_correlations'])}")
```

## Complete analysis workflow

### Step 1: Load and inspect data

```python
import pandas as pd

# Load data
df = pd.read_csv('data.csv')

# Basic inspection
print(f"Shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"\nFirst rows:\n{df.head()}")
print(f"\nData types:\n{df.dtypes}")
print(f"\nMissing values:\n{df.isnull().sum()}")
```

### Step 2: Clean data

```python
def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Clean dataset by handling missing values and duplicates."""
    df_clean = df.copy()

    # Remove duplicates
    df_clean = df_clean.drop_duplicates()

    # Handle missing values
    # For numeric: fill with median
    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        df_clean[col].fillna(df_clean[col].median(), inplace=True)

    # For categorical: fill with mode
    categorical_cols = df_clean.select_dtypes(include=['object']).columns
    for col in categorical_cols:
        df_clean[col].fillna(df_clean[col].mode()[0], inplace=True)

    return df_clean

df_clean = clean_dataset(df)
```

### Step 3: Analyze

```python
# Get summary statistics
summary = analyze_dataset(df_clean)

# Detect outliers
for col in df_clean.select_dtypes(include=[np.number]).columns:
    outliers = detect_outliers(df_clean[col])
    print(f"{col}: {outliers.sum()} outliers detected")

# Check correlations
corr_results = analyze_correlations(df_clean)
print(f"\nStrong correlations:")
for corr in corr_results['strong_correlations']:
    print(f"  {corr['var1']} <-> {corr['var2']}: {corr['correlation']:.3f}")
```

### Step 4: Visualize (optional)

```python
import matplotlib.pyplot as plt

def create_visualization(df: pd.DataFrame, target_col: str):
    """Create comprehensive visualization."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Distribution plot
    axes[0, 0].hist(df[target_col], bins=30, edgecolor='black')
    axes[0, 0].set_title(f'{target_col} Distribution')
    axes[0, 0].set_xlabel(target_col)
    axes[0, 0].set_ylabel('Frequency')

    # Box plot
    axes[0, 1].boxplot(df[target_col])
    axes[0, 1].set_title(f'{target_col} Box Plot')
    axes[0, 1].set_ylabel(target_col)

    # Time series (if applicable)
    axes[1, 0].plot(df.index, df[target_col])
    axes[1, 0].set_title(f'{target_col} Over Time')
    axes[1, 0].set_xlabel('Index')
    axes[1, 0].set_ylabel(target_col)

    # Correlation heatmap
    corr = df.select_dtypes(include=[np.number]).corr()
    im = axes[1, 1].imshow(corr, cmap='coolwarm', aspect='auto')
    axes[1, 1].set_title('Correlation Matrix')
    plt.colorbar(im, ax=axes[1, 1])

    plt.tight_layout()
    plt.savefig(f'{target_col}_analysis.png')
    print(f"Visualization saved to {target_col}_analysis.png")
```

### Step 5: Generate insights

```python
def generate_insights(df: pd.DataFrame, target_col: str) -> list:
    """Generate actionable insights from analysis."""
    insights = []

    # Check data quality
    missing_pct = (df[target_col].isnull().sum() / len(df)) * 100
    if missing_pct > 10:
        insights.append(f"⚠️ High missing data rate: {missing_pct:.1f}%")

    # Check distribution
    skewness = df[target_col].skew()
    if abs(skewness) > 1:
        direction = "right" if skewness > 0 else "left"
        insights.append(f"📊 Distribution is skewed {direction} (skewness: {skewness:.2f})")

    # Check trend
    if len(df) >= 10:
        trend = detect_trend(df[target_col])
        if trend['significant']:
            insights.append(f"📈 Significant {trend['direction']} trend detected (p={trend['p_value']:.4f})")

    # Check outliers
    outliers = detect_outliers(df[target_col])
    outlier_pct = (outliers.sum() / len(df)) * 100
    if outlier_pct > 5:
        insights.append(f"🔍 Outliers detected: {outliers.sum()} ({outlier_pct:.1f}%)")

    # Check variability
    cv = (df[target_col].std() / df[target_col].mean()) * 100
    if cv > 50:
        insights.append(f"📉 High variability detected (CV: {cv:.1f}%)")

    return insights

insights = generate_insights(df_clean, 'sales')
for insight in insights:
    print(insight)
```

## Best practices

1. **Always inspect data first** - Understand structure before analysis
2. **Clean data thoroughly** - Handle missing values, duplicates, outliers
3. **Document assumptions** - Note any data transformations or filters
4. **Validate results** - Cross-check statistical findings
5. **Consider context** - Interpret numbers in business context
6. **Visualize when helpful** - Charts reveal patterns quickly
7. **Check for bias** - Ensure representative sampling

## Common pitfalls

❌ **Correlation ≠ Causation**: High correlation doesn't mean causation
❌ **Cherry-picking**: Don't select only favorable results
❌ **Ignoring outliers**: Investigate outliers, don't just remove them
❌ **Overfitting**: Avoid finding patterns in noise
❌ **Sample size**: Ensure sufficient data for statistical significance

## Related skills

- **code-generation**: For creating analysis scripts
- **text-summarization**: For summarizing findings
- **api-integration**: For fetching external data

## Required libraries

```bash
pip install pandas numpy scipy matplotlib seaborn
```

## References

- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [NumPy Documentation](https://numpy.org/doc/)
- [SciPy Stats](https://docs.scipy.org/doc/scipy/reference/stats.html)
