# Sensitivity Analysis

A Django application for analyzing the sentiment of YouTube video comments.

## Local Setup Guide

Follow these steps to set up and run the project locally.

### 1. Prerequisites
- **Python 3.13** (or newer)
- A **Google Cloud Account** with the **YouTube Data API v3** enabled and a generated API key.


### 2. Installation
1. **Clone the repository:** (Replace `your-repository-url.git` with actual URL)
    ```bash
   git clone https://your-repository-url.git
   
   cd Sensitivity-analysis
    ```
2. **Create and activate a virtual environment** (Recommended)
    ```bash
   python -m venv .venv
   
   # On Windows
   .\.venv\Scripts\activate
   
   # On macOS/Linux
   source .venv/bin/activate
    ```
3. **Install dependencies**

    Install required libraries using command below in terminal:
    ```bash
    pip install -r requirements.txt
    ```
### 3. Environment Configuration (.env)

The application loads secret keys from a `.env` file, which is not included in the repository.
1. Navigate to the Django project directory (the one containing `manage.py`):
    ```bash
   cd .\SensitivityAnalysis\
    ```
2. Create a file named `.env` in this directory.
3. Add your API key from Google Cloud Console to the `.env` file.

Your `.env` file should look like this:
```bash
API_KEY=AIza... (your API key)
```

### 4. Running the Application
1. From `SensitivityAnalysis` directory, run the development server:
    ```bash
   python manage.py runserver
    ```
2. Open your browser and go to `http://localhost:8000/`.

### Database Migrations

If you make changes to the models (in the `models.py` file of any app), you must update the database schema.

1. Make sure you are in the `SensitivityAnalysis` directory.
2. Create the migration files:
    ```bash
   python manage.py makemigrations
    ```
3. Apply the changes to the database:
    ```bash
   python manage.py migrate
    ```
