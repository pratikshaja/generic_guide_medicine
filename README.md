# GenericWise — AI Medicine Comparison Assistant

GenericWise is a healthcare technology project that aims to help users understand the price differences between branded medicines and generic alternatives. It combines medicine information, price comparison, potential savings calculations, and AI-assisted explanations in one web application.

Project status: Development / Prototype

## Overview

Branded medicines and generic alternatives can have different prices. However, comparing medicines requires more than looking at their names or prices.

GenericWise aims to make comparisons more transparent by considering available product information, including active ingredients, strength, dosage form, pack size, and price-source details.

The project also explores how AI can help interpret prescription text and explain medicine-price comparisons in simple language.

## Key Features

- Medicine Search: Search for medicines using available product information.
- Prescription Input:** Explore prescription text and image upload workflows.
- Medicine Extraction:** Identify potential medicine names and related details from input text.
- **Medicine Comparison:** Compare available branded and generic product records.
- **Savings Calculator:** Calculate potential price differences for comparable products.
- **AI Explanation Assistant:** Generate explanations of price differences and factors that may influence brand preference.
- **Safety Checks:** Flag uncertain matches, missing products, and differences in dosage form.
- **Source Transparency:** Display available price-source information and data limitations.

Feature availability may change as development progresses.

## Technology Stack

### Frontend
- React.js
- Vite
- JavaScript
- HTML and CSS
- Bootstrap or other UI libraries used in the project

### Backend
- Python
- Django
- Django REST Framework

### Database
- SQLite for local development, if configured

### AI and Development Tools
- Gemini API or another AI service, depending on the implemented integration
- Git and GitHub
- Postman for API testing

## Project Structure

```text
genericguide/
├── backend/
│   ├── config/
│   ├── core/
│   ├── manage.py
│   └── requirements.txt
├── frontend/
├── data/
├── eval/
├── docs/
├── .gitignore
└── README.md
```

The folders and files shown should reflect the actual repository. Remove entries that do not exist.

## Data Sources and Accuracy

The project is intended to use official medicine-price and product information where access and reuse are permitted.

Potential research sources include:

- [National Pharmaceutical Pricing Authority (NPPA)](https://nppaipdms.gov.in/NPPA/PharmaSahiDaam/searchMedicine)
- [Pradhan Mantri Bhartiya Janaushadhi Pariyojana](https://janaushadhi.gov.in/)

**Prototype limitation:** Sample data may be used during development and testing. Sample prices must not be interpreted as actual market prices. Verified records should retain their source, price type, relevant pack quantity, and reference date wherever available.

## AI Usage

AI may be used to assist with:

- Interpreting prescription text.
- Extracting potential medicine names and attributes.
- Explaining medicine-price differences.
- Supporting development, testing, and prompt refinement.

AI-generated information is not automatically verified. Product matching, price calculations, and safety checks should use explicit validation rules and reliable source data wherever possible.

## Installation and Setup

### Prerequisites

Install the following:

- Python
- Node.js and npm
- Git

### 1. Clone the repository

```bash
git clone https://github.com/pratikshaja/generic_guide_medicine.git
cd generic_guide_medicine
```

### 2. Set up the backend

```bash
cd backend
python -m venv venv
```

Activate the virtual environment on Windows:

```bash
venv\Scripts\activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Configure the required environment variables using a local `.env` file, based on the settings expected by the backend. Do not commit secrets or API keys.

Run database migrations:

```bash
python manage.py migrate
```

Start the development server:

```bash
python manage.py runserver
```

The backend will normally be available at `http://127.0.0.1:8000/`, unless configured differently.

### 3. Set up the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL displayed by Vite in your terminal.

If your frontend requires a backend API URL, configure it using the environment-variable name expected by your application.

## Testing

Testing should cover:

- Medicine search and extraction.
- Missing or uncertain medicine names.
- Product matching and dosage-form mismatches.
- Price-difference and savings calculations.
- Invalid or incomplete input.
- Backend API responses and error handling.
- AI responses that lack sufficient supporting information.

## Safety and Limitations

- GenericWise is an educational prototype, not a medical diagnosis or prescribing system.
- A similar brand name does not establish that two medicines are equivalent.
- Medicine comparisons must consider relevant product attributes and reliable evidence.
- Users should consult a qualified doctor or pharmacist before changing prescribed medicines.
- AI-generated explanations may be incomplete or incorrect and require verification.
- Prescription images may contain sensitive health information and should be handled carefully.

## Future Enhancements

- Import verified product and price records from permitted official sources.
- Improve prescription text extraction and user confirmation.
- Add better product-matching and validation rules.
- Display historical price comparisons where reliable data is available.
- Improve automated tests and deployment.
- Expand prompt documentation and evaluation cases.

## Author

Developed as an AI-assisted healthcare technology project to explore medicine-price transparency, responsible AI integration, and full-stack web development.
