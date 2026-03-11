# Connected Insights

## Introduction
The `connected-insights` skill is a CXO-grade insight engine designed to analyze dashboards, reports, and datasets to produce structured, prescriptive business insights. It supports a wide range of input formats, including CSV, XLSX, PDF, images (PNG/JPG), HTML reports, Markdown, PPTX, Tableau (.twb/.twbx), and Power BI (.pbix). The output adheres to the framework:

1. **What Happened**
2. **Why It Happened**
3. **What Should We Do**
4. **What We'll Achieve**

This skill delivers executive-standard insights, including an executive summary, per-source findings, and a prioritized action plan.

## Integration with OpenClaw
The `connected-insights` skill is fully integrated into the OpenClaw workspace. To integrate it into your system, you need to update the following files:

1. **SOUL.md**:
   - Add a reference to the `connected-insights` skill under the relevant domain (e.g., Decision Science or Data Science).
   - Highlight its purpose as a tool for generating CXO-grade insights.

2. **AGENTS.md**:
   - Include the `connected-insights` skill in the list of available skills.
   - Specify its location in the `skills/` directory and its role in the workspace.

## SOUL.md Content for Integration
To integrate the `connected-insights` skill, add the following content to `SOUL.md` under the relevant domain (e.g., Decision Science or Data Science):

- **Connected Insights**: A CXO-grade insight engine that analyzes dashboards, reports, and datasets to produce structured, prescriptive business insights. It supports decision-making with actionable recommendations and executive-standard findings.

## AGENTS.md Content for Integration
To integrate the `connected-insights` skill, add the following content to `AGENTS.md` under the list of available skills:

- **Skill Name**: `connected-insights`
  - **Description**: Generates CXO-grade insights from dashboards, reports, and datasets.
  - **Location**: `skills/connected-insights/`
  - **Purpose**: Provides structured, data-driven insights to support strategic decision-making.

## Setup Instructions
To integrate the `connected-insights` skill into your system, follow these steps:

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   ```

2. **Place the Skill in the Correct Directory**:
   Ensure the skill is placed in the `skills/` directory of your OpenClaw workspace.

3. **Verify the Workspace Structure**:
   Confirm that the skill's directory structure matches the following:
   ```
   connected-insights/
   ├── SKILL.md
   ├── scripts/
   │   └── insight_generator/
   │       └── pipeline.py
   ```

4. **Update Workspace Files**:
   - Modify `SOUL.md` and `AGENTS.md` as described in the Integration section.

5. **Install Dependencies**:
   Install the required dependencies using the following command:
   ```bash
   pip install -r requirements.txt
   ```

6. **Test the Skill**:
   Run a sample insight generation task to ensure the skill is working correctly.

## Usage Guide

1. **Trigger the Skill**:
   Use the OpenClaw interface to invoke the `connected-insights` skill. Refer to `SKILL.md` for detailed instructions.

2. **Provide Input Data**:
   Ensure the required input data is prepared and formatted as per the skill's requirements.

3. **Generate Insights**:
   Follow the prompts to generate insights. The output will include structured findings and actionable recommendations.

4. **Customize the Output**:
   Modify the `pipeline.py` script in the `scripts/insight_generator/` directory to customize the analysis logic.

## Customization

- **Analysis Logic**: Update the `pipeline.py` script to adjust the insight generation logic or add new features.
- **Skill Metadata**: Modify the `SKILL.md` file to update the skill's description, trigger keywords, or other metadata.

## Support

For assistance with the `connected-insights` skill, please contact the OpenClaw support team or raise an issue in the GitLab repository. Ensure you provide detailed information about the problem and any error messages encountered.

---

By following this README, users can easily integrate and utilize the `connected-insights` skill within their OpenClaw workspace.