from tempfile import NamedTemporaryFile
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from model_loader import analyze_image  # Import the analyze_image function from model_loader

# Create a FastAPI instance
app = FastAPI()

@app.post("/predict/")
async def predict(image: UploadFile = File(...)):
    try:
        # Save the uploaded image to a temporary file
        with NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(await image.read())
            temp_file_path = temp_file.name

        # Analyze the image using the analyze_image function
        predictions = analyze_image(temp_file_path)  # Pass the file path to your model

        # Return the predictions as a JSON response
        return JSONResponse(content={"predictions": predictions})

    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})
