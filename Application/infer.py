# import streamlit as st
# import torch
# from torchvision import transforms
# from PIL import Image

# # Load model
# model = torch.load("model.pth", map_location=torch.device("cpu"))
# model.eval()

# # Define transformation
# transform = transforms.Compose([
#     transforms.Resize((224, 224)),
#     transforms.ToTensor()
# ])

# # Streamlit UI
# st.title("Image Classifier")

# uploaded_file = st.file_uploader("Upload an image", type=["jpg", "png", "jpeg"])

# if uploaded_file:
#     image = Image.open(uploaded_file)
#     st.image(image, caption="Uploaded Image", use_column_width=True)

#     input_tensor = transform(image).unsqueeze(0)  # Add batch dim
#     with torch.no_grad():
#         output = model(input_tensor)
#         prediction = torch.argmax(output, dim=1).item()

#     st.write(f"Prediction: {prediction}")
