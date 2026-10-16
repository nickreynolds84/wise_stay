
# Wise Stay

### AI-Powered Travel Planning Based on What You Want to Experience

**Status:** Active Development — Early Prototype

Wise Stay is an AI-enhanced travel planning application designed to help travelers find hotels based on the experiences they want to have during their trip.

Traditional hotel search platforms prioritize location, price, ratings, and amenities. Wise Stay takes a different approach: **start with the activities and attractions that matter to the traveler, then identify hotels that make those experiences convenient and accessible.**

Rather than simply recommending a hotel in a popular neighborhood, Wise Stay aims to explain *why* a particular hotel is a good fit for a traveler's plans.

The project is being developed as both a practical travel planning tool and a demonstration of applied AI engineering, geographic data processing, and explainable recommendation systems.

---

## The Problem

Finding a hotel in an unfamiliar city can be surprisingly difficult.

Travelers often know what they want to do but don't necessarily know which neighborhoods provide the best access to those activities.

For example, someone visiting New York City might want to:

- Attend Broadway performances
- Visit museums and art galleries
- Explore restaurants and nightlife
- Stay within a specific budget
- Minimize unnecessary travel between activities

Conventional booking platforms allow travelers to filter hotels by price, location, and quality. However, determining whether a hotel is well-positioned for a particular combination of activities often requires substantial additional research.

Wise Stay aims to simplify that process by connecting **travel preferences, geographic intelligence, and hotel recommendations** in one experience.

---

## The Vision

Wise Stay is intended to become a straightforward, activity-driven hotel recommendation application.

A traveler will be able to specify:

- **Destination:** Where they plan to travel
- **Travel dates:** When they will arrive and depart
- **Budget:** Their preferred accommodation spending range
- **Hotel preferences:** Minimum star rating, review quality, and other requirements
- **Activities:** The experiences and attractions they want to prioritize
- **Transportation:** How they expect to get around
- **Occupancy:** The number of travelers and rooms needed

Wise Stay will use those preferences to identify suitable hotels, evaluate their geographic convenience, and provide understandable explanations of the tradeoffs between options.

The goal is not simply to identify the closest hotel to one attraction. It is to find accommodations that offer a strong overall fit for the traveler's combination of interests, budget, and preferences.

**Initial scope:** Hotels only. Vacation rentals are not currently part of the product plan.

---

## How Wise Stay Will Work

The intended recommendation process has five stages.

### 1. Understand the Traveler

The application collects trip requirements and activity preferences.

For example:

> I'm visiting Manhattan for four nights. I want to see Broadway shows, visit art museums, and explore restaurants. I'd prefer a well-reviewed hotel that keeps transportation convenient without exceeding my budget.

### 2. Identify Relevant Attractions

AI models help identify noteworthy attractions associated with the traveler's interests.

For a traveler interested in theater, this could include prominent performance venues and areas with concentrations of theaters.

AI-generated suggestions are treated as candidates, not verified geographic facts.

### 3. Validate Geographic Information

Attraction candidates are matched against geographic points-of-interest data.

Wise Stay uses Overture Maps data as its primary geographic reference for the current prototype.

The matching process accounts for differences in naming, spelling, aliases, and categorization.

Attractions that cannot be sufficiently validated are excluded from automated recommendations or retained for further review.

### 4. Evaluate Hotels

The planned recommendation engine will assess hotels using factors such as:

- Proximity to relevant attractions
- Access to concentrations of desired activities
- Transportation convenience
- Hotel price and availability
- Hotel quality and guest reviews
- Overall alignment with traveler preferences

Hotel scoring will be designed to be deterministic and explainable rather than relying exclusively on an AI model's subjective rankings.

### 5. Explain the Recommendations

AI will generate personalized explanations grounded in validated hotel and geographic information.

Instead of simply displaying a hotel score, Wise Stay aims to explain:

- Why a hotel fits the selected activities
- Which attractions are particularly accessible
- What tradeoffs exist between hotel options
- How budget, quality, and location influence the recommendation

The goal is to make recommendations useful, transparent, and actionable.

---

## Current Development Status

**Last updated: October 16, 2026**

Wise Stay is currently in the early development and validation stage.

The initial geographic focus is **Manhattan, New York City**.

### Implemented or Tested

- Local development environment using Python
- Manhattan points-of-interest dataset from Overture Maps
- Geographic data querying using DuckDB
- Local inference using a quantized Qwen3-4B language model
- Structured JSON generation for attraction discovery
- Name normalization and fuzzy attraction matching
- Geographic candidate validation against Overture records
- Category compatibility checks
- Numeric name-matching safeguards
- Indexed attraction lookup for improved matching performance
- Initial model and matching performance benchmarks
- Preliminary model management and system compatibility utilities

### Initial Validation Results

A prototype evaluation used AI to propose five noteworthy Manhattan theater attractions.

The geographic validation process produced:

| Validation Result | Count |
|---|---:|
| Accepted | 3 |
| Requires review | 1 |
| Rejected | 1 |

The accepted attractions were:

- Palace Theatre
- Studio 54
- Majestic Theatre

Broadhurst Theatre was flagged for review because its Overture category did not align with the expected venue category.

A proposed "42nd Street Theatre" was rejected because it could not be sufficiently matched to an appropriate Overture record.

These results demonstrate the importance of validating AI-generated entities rather than treating model output as authoritative.

### Initial Performance Results

Tests were conducted on an Apple Silicon MacBook with 16 GB RAM.

| Operation | Observed Time |
|---|---:|
| Local model initialization | Approximately 1.8 seconds |
| Structured attraction generation | Approximately 15 seconds |
| Loading and indexing 226,445 Overture POIs | Approximately 3 seconds |
| Matching five attraction candidates | Reported as less than 1 millisecond |

These are preliminary local measurements, not production benchmarks. The matching test primarily exercised exact-name lookups; larger fuzzy-matching workloads still require evaluation.

The project will continue to prioritize responsive performance without introducing unnecessary infrastructure or operating costs.

---

## Technology

The current prototype uses:

| Technology | Purpose |
|---|---|
| Python | Application development and data processing |
| DuckDB | Geographic and analytical data querying |
| Overture Maps | Geographic points-of-interest data |
| RapidFuzz | Attraction name and alias matching |
| llama-cpp-python | Local language model inference |
| Qwen3-4B-Instruct | Initial language model candidate |
| GGUF | Quantized local model format |
| pandas | Data processing and analysis |
| pytest | Automated testing |

Additional technologies will be introduced as the application develops.

Amazon S3 is planned for distributing validated destination intelligence and approved model artifacts.

The user-facing application framework and hotel data providers have not yet been finalized.

---

## AI Philosophy

Wise Stay is designed around a practical principle:

**Use AI where it adds value, and use deterministic systems where precision and consistency matter more.**

AI is intended to support:

1. **Attraction discovery:** Identifying noteworthy places associated with traveler interests.
2. **Personalized explanations:** Communicating why particular hotels fit a traveler's preferences.
3. **Conversational refinement:** Eventually allowing travelers to adjust recommendations through natural-language interaction.

AI is not intended to independently invent geographic locations, hotel prices, availability, or other facts that require reliable external data.

Model-generated attraction candidates must pass geographic validation before they can contribute to automated hotel recommendations.

Likewise, future hotel explanations should be grounded in actual recommendation results.

### Local-First AI

A central project goal is to make useful AI functionality available without requiring a permanently running cloud inference server.

The application is being designed to support approved local models, with optional external AI providers planned for later development.

Local inference offers potential benefits including:

- Reduced recurring inference costs
- Greater user control
- Less dependence on remote inference infrastructure
- Flexibility across supported hardware configurations

Models will be evaluated for accuracy, performance, hardware requirements, and suitability before being approved for use.

The current Qwen model is an **evaluation candidate**, not yet an approved production model.

---

## Getting Started

The repository currently contains development utilities and prototype components rather than a complete end-user application.

The following instructions are intended for developers exploring the project.

### Requirements

- Python 3.10 or newer
- A compatible local development environment
- Sufficient RAM and disk space for local model inference
- Project dependencies
- The required Overture geographic dataset
- A compatible GGUF model for AI inference tests

Hardware requirements will be refined as model evaluations continue.

### Installation

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/wise_stay.git
cd wise_stay
```

Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the project dependencies:

```bash
python -m pip install -r requirements.txt
```

Depending on the operating system and hardware, `llama-cpp-python` may require a platform-specific installation to enable GPU acceleration.

### System Compatibility Check

If the starter utilities are present, inspect the system:

```bash
python demo.py system
python demo.py check
```

These commands provide preliminary information about local hardware suitability.

### Run Tests

```bash
python -m pytest -q
```

### Run Local Attraction Discovery

The current experimental inference script can be run with:

```bash
python test_qwen.py
```

This requires a compatible GGUF model in the configured local model directory and the Manhattan Overture dataset.

The script generates attraction candidates and evaluates them against geographic records.

### Run Geographic Matching Separately

Once a structured attraction candidate file has been generated:

```bash
python test_matching.py
```

This allows developers to test and improve geographic matching without rerunning the language model.

**Note:** These scripts are development tools. They do not yet constitute the final Wise Stay application or user interface.

---

## Planned User Experience

The eventual application should not require travelers to work with Python scripts, geographic datasets, or model configuration files.

The intended experience is:

1. Open Wise Stay.
2. Enter a destination and travel dates.
3. Select a budget, hotel preferences, and activities.
4. Receive hotel recommendations aligned with those preferences.
5. Review explanations and tradeoffs.
6. Refine the recommendations as needed.

The application will handle geographic analysis and AI-assisted processing behind the scenes.

Where local AI is used, the goal is to provide a guided model setup process with clear hardware compatibility information.

An optional model-retention setting is planned so users can choose whether to keep downloaded model files for future sessions.

---

## Development Roadmap

### Phase 1 — Geographic Intelligence and AI Validation

**In progress**

- [x] Establish Manhattan as the initial pilot destination
- [x] Load Overture points-of-interest data
- [x] Test local language model inference
- [x] Generate structured attraction candidates
- [x] Implement geographic name matching
- [x] Add category and numeric identity safeguards
- [x] Introduce indexed attraction matching
- [ ] Resolve ambiguous attraction records
- [ ] Expand fuzzy-matching evaluation
- [ ] Strengthen geographic boundary validation
- [ ] Evaluate attraction discovery across multiple activity categories

### Phase 2 — Hotel Recommendation Engine

**Planned**

- [ ] Integrate reliable hotel data
- [ ] Support date-specific pricing and availability
- [ ] Incorporate hotel quality and review information
- [ ] Implement activity-based geographic scoring
- [ ] Incorporate transportation considerations
- [ ] Rank hotels using explainable scoring logic
- [ ] Test recommendation quality against realistic travel scenarios

### Phase 3 — Personalized AI Explanations

**Planned**

- [ ] Generate explanations grounded in verified recommendation data
- [ ] Compare local model candidates
- [ ] Evaluate accuracy, latency, and resource consumption
- [ ] Introduce model approval criteria
- [ ] Support additional AI provider options where practical

### Phase 4 — User-Facing Application

**Planned**

- [ ] Develop an intuitive trip-planning interface
- [ ] Connect user preferences to the recommendation engine
- [ ] Present hotel rankings and explanations
- [ ] Support recommendation refinement
- [ ] Improve installation and onboarding
- [ ] Conduct end-to-end testing with real travel scenarios

### Phase 5 — Expansion and Refinement

**Future**

- [ ] Add additional destinations
- [ ] Expand activity categories
- [ ] Introduce reusable destination intelligence
- [ ] Improve model distribution and caching
- [ ] Refine recommendations using user feedback
- [ ] Evaluate additional deployment and distribution options

The roadmap is directional and may evolve as technical and product decisions are validated.

---

## Project Principles

Wise Stay is being developed with several priorities.

**Practical usefulness**

The application should solve a real travel planning problem rather than simply demonstrate AI capabilities.

**Grounded recommendations**

Geographic locations, hotel attributes, and other factual inputs should come from appropriate data sources.

**Explainability**

Users should understand why a hotel was recommended and what tradeoffs they are making.

**Performance**

The application should remain responsive on supported hardware and avoid unnecessary computation.

**Cost efficiency**

The architecture should minimize recurring infrastructure and AI inference costs, particularly during early development.

**Modularity**

AI models, geographic data providers, and hotel data providers should be replaceable without requiring a complete application redesign.

**Responsible AI integration**

Language models should be evaluated, constrained, and validated rather than treated as inherently reliable sources of factual information.

---

## Documentation

This README provides the project overview, current status, and basic developer instructions.

Detailed technical documentation will be maintained in the project's GitHub Wiki as development progresses.

Planned Wiki topics include:

- System architecture
- Geographic data ingestion and processing
- Attraction clustering and destination intelligence
- AI model evaluation and selection
- Entity matching and validation
- Hotel scoring methodology
- Performance benchmarks
- Data storage and caching
- Design decisions and tradeoffs

---

## Project Status and Limitations

Wise Stay is an active work in progress.

At present:

- There is no completed hotel recommendation interface.
- Live hotel pricing and availability have not been integrated.
- The local AI model remains under evaluation.
- Geographic matching requires additional edge-case testing.
- The initial implementation focuses on Manhattan.
- Production deployment and distribution are not yet available.

The project is being developed incrementally, with functionality evaluated before it becomes part of the user-facing application.

---

## Data and Model Attribution

Geographic points-of-interest data is sourced from **[Overture Maps](https://overturemaps.org/)**. Applicable attribution and licensing requirements will be maintained as the project develops.

Local AI experiments currently use a quantized version of **[Qwen3-4B-Instruct-2507](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)** through `llama-cpp-python`.

Model redistribution rights and artifact provenance will be reviewed before any model weights are distributed through Wise Stay.

Model weights and large geographic datasets are not intended to be committed directly to the Git repository.

---

## License

A project license has not yet been selected.

Until a license is added, no open-source usage rights are granted by default.

---

**Wise Stay — Find the right place to stay for the experiences that matter.**
