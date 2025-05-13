from fastapi import FastAPI, File, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from model_loader import analyze_image

# Initialize FastAPI instance
app = FastAPI()

class ModelUpdate(BaseModel):
    model_path: str = "/app/shared_models/best.pt"

@app.get("/")
async def root():
    return {"message": "AI Model Prediction Service"}

@app.post("/predict/")
async def predict_endpoint(image: UploadFile = File(...)):
    try:
        # Read the uploaded image
        image_data = await image.read()
        
        # Analyze the image using the loaded model
        predictions = analyze_image(image_data)
        
        # Return the predictions
        return {
            "success": True,
            "predictions": predictions
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
