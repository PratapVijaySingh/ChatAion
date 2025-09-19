# Virtual Human Project Setup Guide

This guide will walk you through setting up the complete Virtual Human AI-powered avatar system.

## Prerequisites

- Python 3.8+
- Node.js 16+
- Unity 2022.3 LTS or newer
- OpenAI API key
- ElevenLabs API key
- Git

## Project Structure

```
VirtualHuman/
├── backend/                 # Python FastAPI backend
│   ├── api/                # API endpoints
│   ├── core/               # Core services
│   └── main.py             # Main application
├── frontend/               # React web interface
├── unity/                  # Unity3D project
├── requirements.txt        # Python dependencies
├── env.example            # Environment variables template
└── README.md              # Project documentation
```

## Step 1: Backend Setup

### 1.1 Create Virtual Environment
```bash
cd VirtualHuman
python -m venv venv
venv\Scripts\activate  # Windows
# OR
source venv/bin/activate  # Linux/Mac
```

### 1.2 Install Dependencies
```bash
pip install -r requirements.txt
```

### 1.3 Configure Environment Variables
```bash
cp env.example .env
# Edit .env with your API keys:
# OPENAI_API_KEY=your_openai_key_here
# ELEVENLABS_API_KEY=your_elevenlabs_key_here
```

### 1.4 Start Backend Server
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

## Step 2: Frontend Setup

### 2.1 Install Dependencies
```bash
cd frontend
npm install
```

### 2.2 Start Development Server
```bash
npm start
```

The frontend will be available at `http://localhost:3000`

## Step 3: Unity Setup

### 3.1 Open Unity Hub
1. Open Unity Hub
2. Click "Open" → "Add project from disk"
3. Navigate to `VirtualHuman/unity/` and select it

### 3.2 Install Required Packages
1. Open the project in Unity
2. Go to Window → Package Manager
3. Install the following packages:
   - TextMeshPro
   - Input System
   - WebGL Build Support

### 3.3 Configure Avatar
1. Import your 3D avatar model (FBX format recommended)
2. Ensure the model has proper blendshapes for facial expressions
3. Add the `AvatarController` script to your avatar GameObject
4. Assign the SkinnedMeshRenderer and Animator components

### 3.4 Setup WebSocket Connection
1. Add the `WebSocketManager` script to a GameObject in your scene
2. Configure the WebSocket URL to match your backend
3. Ensure the avatar has the `AvatarController` script attached

## Step 4: Testing the System

### 4.1 Test Backend
```bash
curl http://localhost:8000/health
```

### 4.2 Test Frontend
1. Open `http://localhost:3000` in your browser
2. Enter your OpenAI API key
3. Select an avatar and start chatting

### 4.3 Test Unity Integration
1. Start your Unity scene
2. Check the console for WebSocket connection status
3. Send a message from the frontend
4. Watch the avatar animate in response

## Configuration Options

### Avatar Personalities
The system includes several pre-configured avatar personalities:
- **Default**: Friendly and helpful
- **Teacher**: Educational and encouraging
- **Assistant**: Professional and efficient

### Animation Settings
- **Blendshape Transition Speed**: Controls how quickly facial expressions change
- **Gesture Transition Speed**: Controls how quickly gestures animate
- **Animation FPS**: Target frame rate for animations

### Audio Settings
- **Voice Selection**: Choose from available ElevenLabs voices
- **Emotion Detection**: Automatic voice parameter adjustment based on content
- **Real-time Processing**: Enable/disable live audio processing

## Troubleshooting

### Common Issues

#### Backend Won't Start
- Check if port 8000 is available
- Verify all dependencies are installed
- Check environment variables are set correctly

#### Frontend Connection Issues
- Ensure backend is running on port 8000
- Check browser console for CORS errors
- Verify proxy settings in package.json

#### Unity Connection Issues
- Check WebSocket URL configuration
- Verify backend is running and accessible
- Check Unity console for connection errors

#### Audio Issues
- Verify OpenAI and ElevenLabs API keys
- Check audio file permissions
- Ensure proper audio format support

### Debug Mode
Enable debug mode by setting `DEBUG=true` in your `.env` file for detailed logging.

## Performance Optimization

### Backend
- Use Redis for caching (optional)
- Implement connection pooling
- Monitor memory usage

### Frontend
- Implement message pagination
- Use WebSocket for real-time updates
- Optimize bundle size

### Unity
- Limit blendshape updates per frame
- Use LOD (Level of Detail) for complex models
- Optimize animation curves

## Deployment

### Production Considerations
- Use HTTPS for all connections
- Implement proper authentication
- Set up monitoring and logging
- Use production-grade databases
- Implement rate limiting

### Cloud Deployment
- Backend: Deploy to AWS, Azure, or Google Cloud
- Frontend: Deploy to Vercel, Netlify, or similar
- Unity: Build for target platforms (Windows, Mac, Linux)

## Support and Contributing

For issues and contributions:
1. Check existing issues
2. Create detailed bug reports
3. Follow the coding standards
4. Test thoroughly before submitting

## License

This project is licensed under the MIT License - see LICENSE file for details. 