# Titan vs Nova - AWS Bedrock Model Comparison

A Streamlit application for comparing AWS Bedrock's Titan and Nova AI models, featuring text generation and image/video creation capabilities.

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/titan-vs-nova.git
cd titan-vs-nova
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install required dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.streamlit/secrets.toml` file with your AWS credentials:
```toml
[aws]
iam_access_key_id = "YOUR_ACCESS_KEY_ID"
iam_secret_key = "YOUR_SECRET_ACCESS_KEY"
```

5. Run the application:
```bash
streamlit run app.py
```

## Features

### Text Generation
- Compare responses from different Titan and Nova models
- Customizable system prompts and user inputs
- Multiple model variants:
    - Titan: Express, Lite, and Premiere
    - Nova: Micro, Lite, and Pro

### Image & Video Generation
- Generate images using Nova Canvas
- Create videos using Nova Reels
- Supports custom prompts and configurations

## Code Structure

The application consists of two main components:

1. **Model Comparison Tab**
     - Allows side-by-side comparison of Titan and Nova model responses
     - Handles asynchronous API calls to AWS Bedrock
     - Displays formatted results

2. **Image & Video Generation Tab**
     - Integrates with Nova Canvas for image generation
     - Supports video creation through Nova Reels
     - Includes progress tracking and error handling

## Requirements

- Python 3.7+
- Streamlit
- Boto3
- Pillow
- AWS Bedrock access