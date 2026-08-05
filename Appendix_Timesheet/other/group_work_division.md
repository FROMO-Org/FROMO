# Group Paper Work Division

This work division is based on the required paper structure and the five project roles: **Backend**, **Data & ML**, **Frontend**, **Mobile**, and **Product**.

## Overall Responsibility

The **Product** role should act as the main editor. This person is responsible for keeping the paper coherent, checking the storyline, controlling the page limit, and making sure all sections connect smoothly.

## Role-Based Division

| Role | Main Sections | Responsibilities |
|---|---|---|
| Product | Abstract, Introduction, Conclusion and Future Work | Define the problem, motivation, objectives, project contribution, application URL, limitations, future work, and overall narrative. |
| Backend | Methodology, Evaluation and Results | Explain backend architecture, API design, database, authentication, deployment, server-side logic, reliability, and backend testing. |
| Data & ML | Data Analytics and Visualization, Evaluation and Results | Describe datasets, data cleaning, preprocessing, feature engineering, models, algorithms, analytical methods, visualizations, insights, and model/data evaluation. |
| Frontend | Methodology, Data Visualization, Evaluation and Results | Explain web interface design, frontend architecture, frameworks, dashboard components, user interaction, visualization implementation, and frontend testing. |
| Mobile | Methodology, Evaluation and Results | Explain mobile responsiveness, mobile interface decisions, cross-device compatibility, mobile usability, performance on smaller screens, and mobile testing. |

## Section Ownership

### Abstract
**Lead: Product**
- Summarize the problem, objectives, methodology, key findings, and application URL.
- Write this section last, after all other sections are complete.

### 1. Introduction
**Lead: Product**
- Introduce the project context and motivation.
- Clearly state the problem or challenge.
- Define the target users or stakeholders.
- Present the project objectives and main contributions.
- End with a brief roadmap of the paper.

### 2. Literature Review
**Lead: Product, with input from all roles**
- Product organizes the structure and writing.
- Backend contributes sources about system architecture or backend technologies.
- Data & ML contributes sources about datasets, analytics, visualization, or machine learning methods.
- Frontend contributes sources about dashboard design, web usability, or visualization interfaces.
- Mobile contributes sources about responsive design, mobile usability, or cross-device systems.

#### Literature Review Source Division

Each role should provide **2--3 high-quality sources**. These can include academic papers, official documentation, technical standards, credible case studies, or existing applications. Product will combine these into one coherent literature review instead of listing them separately.

| Role | What to Find | Suggested Source Types | How It Supports the Paper |
|---|---|---|---|
| Product | Sources about the problem domain, target users, existing market/application gap, and similar products. | Academic papers about the domain; reports from trusted organizations; competitor applications; official product pages; user need studies. | Explains why the problem matters and positions the project against existing solutions. |
| Backend | Sources about backend architecture, REST APIs, databases, authentication, cloud deployment, scalability, or security. | Official framework documentation; cloud provider documentation; database documentation; API design guidelines; software architecture papers. | Justifies backend design choices and shows the technical approach is appropriate. |
| Data & ML | Sources about datasets, data preprocessing, analytics methods, ML models, evaluation metrics, and data visualization theory. | Dataset documentation; ML papers; official library documentation; analytics method papers; visualization research. | Justifies the data pipeline, model/algorithm selection, and interpretation of results. |
| Frontend | Sources about dashboard design, web usability, visual analytics, accessibility, UI frameworks, and frontend visualization libraries. | HCI papers; dashboard design papers; official frontend framework documentation; visualization library documentation; accessibility guidelines. | Supports interface design choices and explains how users interact with data insights. |
| Mobile | Sources about responsive web design, mobile usability, cross-device interaction, progressive web apps, and mobile performance. | Mobile HCI papers; responsive design guidelines; PWA documentation; mobile UX guidelines; browser/device compatibility documentation. | Justifies mobile design decisions and shows the application works across devices. |

#### Literature Review Structure

- **Problem and user need:** Led by Product; explains the project context and why the application is needed.
- **Existing systems and applications:** Led by Product, Frontend, and Mobile; compares similar tools and identifies limitations.
- **Technical approaches:** Led by Backend, Data & ML, and Frontend; discusses relevant architectures, analytics techniques, and visualization methods.
- **Research gap and project positioning:** Led by Product; explains how this project is similar to and different from existing work.

#### Source Summary Format

Each person should submit sources to Product using this format:

```md
### Source Title
Role:
Full citation or link:
Type of source: academic paper / official documentation / case study / application / report
Key idea:
How it relates to our project:
Limitation or gap:
Possible sentence for the literature review:
```

### 3. Methodology
**Leads: Backend, Frontend, Mobile**
- Backend explains the server-side design, database, API, deployment, and backend technology choices.
- Frontend explains the web interface, frontend framework, user flow, dashboard, and visualization components.
- Mobile explains responsive design, mobile layout decisions, and cross-device compatibility.
- Product helps connect these parts into one coherent system architecture story.

### 4. Data Analytics and Visualization
**Lead: Data & ML**
- Describe the dataset source, size, variables, and limitations.
- Explain data cleaning, preprocessing, transformation, and feature engineering.
- Explain models, algorithms, or analytical techniques.
- Justify why these techniques were chosen.
- Present the main visualizations and explain the insights.
- Frontend supports this section by explaining how visualizations are displayed in the application.

### 5. Evaluation and Results
**Shared section; Product edits final version**
- Backend reports backend tests, API reliability, deployment status, and performance metrics.
- Data & ML reports model/data evaluation, analytical results, and interpretation.
- Frontend reports UI testing, usability feedback, and visualization correctness.
- Mobile reports mobile testing, responsive design results, and cross-device feedback.
- Product combines all evidence into a clear discussion of whether the project was successful.

### 6. Conclusion and Future Work
**Lead: Product, with input from all roles**
- Summarize what the project achieved.
- Highlight the key technical and analytical findings.
- Be self-critical about limitations and weaknesses.
- Include future improvements from each role:
  - Backend: scalability, security, database, deployment, API improvements.
  - Data & ML: better data, improved models, additional analytics, more evaluation.
  - Frontend: better interface design, accessibility, visualization improvements.
  - Mobile: improved mobile UX, device testing, app-like features.
  - Product: stronger user validation, clearer product direction, stakeholder feedback.

## Suggested Page Budget

| Section | Suggested Length |
|---|---:|
| Abstract | 150--250 words |
| Introduction | 0.75--1 page |
| Literature Review | 1--1.25 pages |
| Methodology | 1.5--2 pages |
| Data Analytics and Visualization | 1.5--2 pages |
| Evaluation and Results | 1--1.25 pages |
| Conclusion and Future Work | 0.5--0.75 page |
| References | Not included in the 8-page limit |

## Recommended Workflow

1. Product creates the shared outline and confirms the paper storyline.
2. Each role writes bullet points first, not full paragraphs.
3. The team agrees on figures, tables, and screenshots before writing final text.
4. Each role writes their assigned section draft.
5. Product merges all sections and standardizes tone, terminology, and formatting.
6. Everyone reviews the final paper for technical accuracy.
7. Product performs the final edit for grammar, flow, citations, and page limit.

## Final Checklist

- The problem is clearly explained.
- The technical approach is justified.
- Alternatives are discussed where relevant.
- The data analytics work is clearly connected to the application.
- Evaluation includes both technical results and user/system feedback.
- The conclusion is self-critical and includes realistic future work.
- The paper has a clear storyline rather than reading like a diary of tasks.
