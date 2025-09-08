# Project Instructions: Expat Insurance Configurator & Comparison Platform

## 1. Core Objective

You will build a web application that serves as a database and comparison tool for expat insurance products. The final goal is to power the website `expatverzekering.nl`.

The project will evolve in three phases:

*   **Internal Knowledge Base:** An admin interface for employees to manage and query all insurance product data. This is the primary focus.
*   **AI Agent Logic:** The backend logic that can find and recommend the best insurance package based on variable user input.
*   **Public UI:** A customer-facing website for self-service comparison and configuration.

## 2. Technology Stack

*   **Backend Framework:** Python with Django.
*   **Database:** PostgreSQL (due to heavy use of JSONB).
*   **Local Development:** Use Docker for the PostgreSQL instance to ensure consistency with production. Use a Python virtual environment (`venv`) and manage dependencies in `requirements.txt`.
*   **Version Control:** Use Git.

## 3. Database Architecture (CRITICAL)

Your primary task is to implement the provided database schema, which functions as a flexible **Product Configurator Model**.

### Key Architectural Concepts to implement:

*   **Standardized Library Tables:** These are our "master lists" and must be generic.
    *   `Modules`: High-level commercial product components (e.g., "Medical", "Baggage").
    *   `CoverageCategories` & `CoverageItems`: Our standardized, hierarchical "dictionary" of all possible coverage details (e.g., Category: "Electronics", Item: "Laptop").

*   **Product-Specific Implementation Tables:** These tables link a specific product to our standard library.
    *   `ProductModules`: Links a provider's product to one of our standard `Modules`.
    *   `CoverageItemDetails`: Defines the actual coverage amount for a `CoverageLevel` and a `CoverageItem`.

*   **Parametric Pricing Engine:** This is the most complex part. The price is determined by a combination of factors.
    *   `PremiumParameters`: The factors that influence a price (e.g., "Deductible", "Age Group", "Coverage Region").
    *   `ParameterOptions`: The possible values for each parameter.

## 4. Initial Development Steps

### Project Structure:

```
.
├── expat_project/
│   ├── settings.py
│   └── urls.py
├── comparator_app/
│   ├── models.py
│   ├── admin.py
│   ├── views.py
│   └── urls.py
└── manage.py
```

### Implementation Steps:

1.  **Create Models:** In `comparator_app/models.py`, define all tables from our schema as Django models. Pay close attention to `ForeignKey`, `ManyToManyField` (for `ProductTargetAudiences`), and `JSONField` (for JSONB).
2.  **Build the Internal Knowledge Base:** In `comparator_app/admin.py`, register all your models with the Django admin site (`admin.site.register(...)`). This will automatically generate a functional web UI for data entry and management, which serves as our Phase 1 goal.

## 5. Key Logic for Implementation

*   **Handle Different Product Structures:** The model must support both "vertical" (Goudse-style, independent modules) and "horizontal" (ISIS-style, overarching levels) products.
    *   For ISIS-style products, the main product level (e.g., "Europa Super+") must be a `PremiumParameter` that influences the price of optional `ProductModules` like "Geneeskundige Kosten". The application logic will pass this choice as a context when calculating the price of the optional module.

*   **Differentiate Presentation:**
    *   **Product Detail View:** The UI should follow the insurer's structure. This is derived from the `ProductModule` and the commercial sub-categories defined by the `CoverageCategory` hierarchy.
    *   **Comparison View:** The UI must use our standardized `CoverageItems` and `CoverageCategories` to create an objective, apples-to-apples comparison table.