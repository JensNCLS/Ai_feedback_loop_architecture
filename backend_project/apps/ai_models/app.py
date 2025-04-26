from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from model_loader import analyze_image, reload_model

# Initialize FastAPI instance
app = FastAPI()

@app.get("/")
async def root():
    return {"message": "FastAPI server is running!"}

@app.post("/predict/")
async def predict(image: UploadFile = File(...)):
    try:
        image_file = await image.read()

        predictions = analyze_image(image_file)

        return JSONResponse(content={"predictions": predictions})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

@app.post("/reload-model/")
async def reload_model_endpoint():
    """Endpoint to reload the model without restarting the container."""
    try:
        result = reload_model()
        return JSONResponse(content={"status": "success", "message": result})
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "failure", "message": str(e)})
