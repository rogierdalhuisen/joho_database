# Expat Insurance Configurator & Comparison Platform

## 1. Introduction

This project is a sophisticated web application designed to digitize, configure, and compare complex expat insurance products. The ultimate goal is to power the backend systems and user-facing comparison tools for expatverzekering.nl.

The architecture is built around a flexible Product Configurator Data Model, capable of handling diverse and complex product structures from various insurance providers.

## 2. Core Features

The development is planned in three evolutionary phases:

*   **Internal Knowledge Base:** A robust Django admin interface that serves as a central source of truth for employees. It allows for detailed data entry and management of all insurance products, modules, coverage details, and pricing rules.
*   **AI Agent Logic:** A backend service that leverages the structured database to intelligently find, configure, and recommend the optimal insurance package based on variable customer data (e.g., age, destination, specific coverage needs).
*   **Public UI:** A customer-facing website that utilizes the backend logic to provide a self-service comparison and configuration experience for end-users.

## 3. Technology Stack

*   **Backend Framework:** Python 3.11+ with Django 5.x
*   **Database:** PostgreSQL 16+ (leveraging JSONB for flexible data storage)
*   **Local Development Environment:** Docker & Docker Compose
*   **Dependency Management:** `pip` with `requirements.txt`
*   **Version Control:** Git

## 4. Data Model Overview

The database architecture is the core of this project. It is designed to be highly flexible and scalable. Key concepts include:

*   **Standardized Library Tables (`Modules`, `CoverageItems`):** A universal, internal "dictionary" of all possible insurance components and coverage details. This is the key to enabling objective, apples-to-apples comparisons.
*   **Product-Specific Implementation Tables (`ProductModules`, `CoverageItemDetails`):** These tables link a specific insurer\'s product to our standardized library, effectively "translating" their marketing structure into our canonical format.

## 5. Getting Started

### Prerequisites

*   Python 3.11+
*   Docker & Docker Compose
*   Git

### Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd expatverzekering-project
    ```

2.  **Set up Python Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file in the root directory by copying the example file. This will contain your local database credentials.
    ```bash
    cp .env.example .env
    ```
    Update the `.env` file with your preferred local database credentials.

5.  **Start the Database:**
    Use Docker Compose to start the PostgreSQL database container in the background.
    ```bash
    docker-compose up -d
    ```

6.  **Run Database Migrations:**
    Apply the database schema to your local PostgreSQL instance.
    ```bash
    python manage.py migrate
    ```

7.  **Create a Superuser:**
    Create an admin account to access the internal knowledge base (Django Admin).
    ```bash
    python manage.py createsuperuser
    ```
    Follow the prompts to create your admin user.

8.  **Run the Development Server:**
    ```bash
    python manage.py runserver
    ```
    The application is now running at `http://127.0.0.1:8000/`. You can access the internal knowledge base at `http://127.0.0.1:8000/admin/`.

## 6. Project Structure

*   `expat_project/`: Contains the main project configuration (`settings.py`, `urls.py`).
*   `comparator_app/`: The core application containing the logic for the insurance comparison tool.
    *   `models.py`: Defines the database schema as Django models.
    *   `admin.py`: Configures the Django admin interface (our internal knowledge base).
    *   `views.py`: Contains the application logic for handling requests and returning responses.