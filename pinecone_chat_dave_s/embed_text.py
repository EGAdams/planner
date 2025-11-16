  
  
import tensorflow_hub as hub

# Load the Universal Sentence Encoder
encoder = hub.load('https://tfhub.dev/google/universal-sentence-encoder/4')

# Get the 'message' field from the provided data
text = 'hello'

# Convert the text into vector form
vector = encoder([text]).numpy()

# Check the shape of the vector
vector.shape
