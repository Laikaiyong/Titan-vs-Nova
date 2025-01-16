import streamlit as st
import boto3
import json
import base64
import io
import logging
from PIL import Image
from botocore.config import Config
import asyncio
from concurrent.futures import ThreadPoolExecutor

def get_bedrock_client():
    bedrock = boto3.client(
        service_name='bedrock-runtime',
        aws_access_key_id=st.secrets["aws"]["iam_access_key_id"],
        aws_secret_access_key=st.secrets["aws"]["iam_secret_key"],
        region_name='us-east-1'
    )
    return bedrock

# Model configurations
titan_models = {
    "Titan Text Express": "amazon.titan-text-express-v1",
    "Titan Text Lite": "amazon.titan-text-lite-v1",
    "Titan Text Premiere": "amazon.titan-text-premier-v1:0"
}

nova_models = {
    "Nova Micro": "amazon.nova-micro-v1:0",
    "Nova Lite": "amazon.nova-lite-v1:0	",
    "Nova Pro": "amazon.nova-pro-v1:0"
}

st.set_page_config(layout="wide", page_title="🤖 Titan vs Nova")
st.title("🤖 AWS Bedrock - Titan vs Nova Comparison")

bedrock_client = get_bedrock_client()

tab1, tab2 = st.tabs(["💬 Model Comparison", "🎨 Image & Video Generation"])


with tab1:
    st.subheader("Compare Model Responses")
    
    system_prompt = st.text_area("System Instructions (Optional)", height=100)
    user_prompt = st.text_input("Your prompt")
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_titan = st.selectbox("Select Titan Model", list(titan_models.keys()))
    with col2:
        selected_nova = st.selectbox("Select Nova Model", list(nova_models.keys()))
    
    if st.button("Generate Responses"):
        if user_prompt:
            col1, col2 = st.columns(2)
            
            async def get_titan_response(bedrock_client, model_id, request):
                try:
                    response = bedrock_client.invoke_model(
                        modelId=model_id,
                        body=json.dumps(request)
                    )
                    response_body = json.loads(response['body'].read())
                    return response_body['results'][0]['outputText']
                except Exception as e:
                    return f"Error with Titan: {str(e)}"

            async def get_nova_response(bedrock_client, model_id, system_prompt, request):
                try:
                    response = bedrock_client.converse(
                        modelId=model_id,
                        system=[{ "text": system_prompt }],
                        messages=request
                    )
                    return response['output']["message"]["content"][0]["text"]
                except Exception as e:
                    return f"Error with Nova: {str(e)}"

            titan_request = {
                "inputText": f"{system_prompt}\n{user_prompt}" if system_prompt else user_prompt,
                "textGenerationConfig": {
                    "temperature": 0.7,
                    "topP": 0.9,
                }
            }

            nova_request = [
                { "role": "user", "content": [{"text": user_prompt}] }
            ]

            with ThreadPoolExecutor() as executor:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                tasks = [
                    get_titan_response(bedrock_client, titan_models[selected_titan], titan_request),
                    get_nova_response(bedrock_client, nova_models[selected_nova], system_prompt, nova_request)
                ]
                titan_result, nova_result = loop.run_until_complete(asyncio.gather(*tasks))
                loop.close()

            with col1:
                st.markdown("### Titan Response")
                st.write(titan_result)
            
            with col2:
                st.markdown("### Nova Response")
                st.write(nova_result)

with tab2:
    st.subheader("🎨 Nova Image & Video Generation")
    
    image_prompt = st.text_input("✍️ Enter prompt for image/video generation")
    media_generate = st.button("🚀 Generate")
    
    col1, col2 = st.columns(2)
    
    async def generate_image(prompt):
        try:
            image_request = {
                "taskType": "TEXT_IMAGE",
                "textToImageParams": {
                    "text": prompt
                },
                "imageGenerationConfig": {
                    "numberOfImages": 1,
                    "height": 1024,
                    "width": 1024,
                    "cfgScale": 8.0,
                    "seed": 0
                }
            }
            
            response = bedrock_client.invoke_model(
                modelId="amazon.nova-canvas-v1:0",
                body=json.dumps(image_request),
                accept="application/json",
                contentType="application/json"
            )
            response_body = json.loads(response['body'].read())
            
            return response_body
        except Exception as e:
            return {"error": str(e)}

    async def generate_video(prompt):
        try:
            video_request = {
                "taskType": "TEXT_VIDEO",
                "textToVideoParams": {
                    "text": prompt
                },
                "videoGenerationConfig": {
                    "durationSeconds": 6,
                    "fps": 24,
                    "dimension": "1280x720",
                    "seed": 0
                }
            }
            response = bedrock_client.start_async_invoke(
                modelId="amazon.nova-reel-v1:0",
                modelInput=video_request,
                outputDataConfig={
                    "s3OutputDataConfig": {
                        "s3Uri": "s3://nova-vandyck"
                    }
                }
            )
            return response['ResponseMetadata']['RequestId']
        except Exception as e:
            return {"error": str(e)}

    async def wait_for_video(job_id, max_attempts=30):
        s3 = boto3.client('s3')
        bucket = "nova-vandyck"
        video_key = f"{job_id}/output.mp4"
        
        for _ in range(max_attempts):
            try:
                response = s3.get_object(Bucket=bucket, Key=video_key)
                return response['Body'].read()
            except s3.exceptions.NoSuchKey:
                await asyncio.sleep(10)  # Wait 10 seconds before next attempt
        
        return None

    if media_generate and image_prompt:
        with ThreadPoolExecutor() as executor:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            with col1:
                st.markdown("### 🎨 Nova Canvas (Image Generation)")
                with st.spinner("🎨 Generating image..."):
                    image_result = loop.run_until_complete(generate_image(image_prompt))
                    
                    if 'images' in image_result:
                        base64_image = image_result['images'][0]
                        image_bytes = base64.b64decode(base64_image)
                        st.image(image_bytes)
                    if 'error' in image_result:
                        st.error(f"❌ Error generating image: {image_result['error']}")
            
            with col2:
                st.markdown("### 🎥 Nova Reels (Video Generation)")
                with st.spinner("🎥 Generating video..."):
                    job_id = loop.run_until_complete(generate_video(image_prompt))
                    
                    if isinstance(job_id, str):
                        st.info(f"🎬 Video generation started. Job ID: {job_id}")
                        
                        # Wait for video with progress bar
                        progress_bar = st.progress(0)
                        video_bytes = loop.run_until_complete(wait_for_video(job_id))
                        
                        if video_bytes:
                            st.success("✅ Video generated successfully!")
                            st.video(video_bytes)
                        else:
                            st.warning("⏳ Video generation taking longer than expected. Please check back later.")
                    else:
                        st.error(f"❌ Error starting video generation: {job_id.get('error')}")
            
            loop.close()
