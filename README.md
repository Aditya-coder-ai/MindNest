# MindNest 🌿

MindNest is a personalized, AI-powered mood companion and journaling web application. It helps users track their daily emotions, understand their mental wellness through interactive insights, and grow via supportive reflections. 

## Features
- **Daily Mood Tracking**: Log your feelings with a rich, interactive interface using tailored emojis and descriptive mood labels.
- **Journaling**: A private space to write down your thoughts.
- **AI Wellness Assistant**: A supportive chat companion that provides quick, empathetic guidance based on the emotions you express.
- **Gemini GenAI Chat**: The wellness assistant now uses Gemini through the Flask backend.
- **Insights & Analytics**: Visualize your mood trends over time with beautiful, interactive graphs using Chart.js.
- **Responsive Design**: Carefully crafted, modern UI that works perfectly across desktops, tablets, and mobile devices.
- **Firebase Integration**: Supports cloud persistence so you don't lose your data.

## Tech Stack
- **Frontend Framework**: React 19 + Vite
- **Styling**: Vanilla CSS with modern custom variables, flexbox/grid layouts, and micro-animations.
- **Routing**: React Router DOM v7
- **Data Visualization**: Chart.js and `react-chartjs-2`
- **Backend/Storage**: Firebase v12

## Getting Started

### Prerequisites
Make sure you have [Node.js](https://nodejs.org/) installed on your machine.

### Installation

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone <your-repository-url>
   cd MindNest
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Set up the AI backend**:
   ```bash
   cd ai-backend
   pip install -r requirements.txt
   ```

4. **Configure Gemini GenAI**:
   Set a Gemini API key before starting the backend.

   Windows PowerShell:
   ```powershell
   $env:GEMINI_API_KEY="your_api_key_here"
   ```

   Optional:
   ```powershell
   $env:GEMINI_MODEL="gemini-2.5-flash"
   ```

5. **Configure Firebase**:
   Ensure your `firebase-config.json` is correctly set up with your Firebase project credentials.

6. **Start the AI backend**:
   ```bash
   cd ai-backend
   python app.py
   ```

7. **Start the development server**:
   ```bash
   npm run dev
   ```

8. **Open in browser**:
   Navigate to `http://localhost:5173` to view the app in your browser.

## Available Scripts

- `npm run dev`: Starts the development server.
- `npm run build`: Bundles the app into static files for production.
- `npm run lint`: Runs ESLint to catch potential issues and enforce code quality.
- `npm run preview`: Locally previews the production build.

## Project Structure
- `src/components/`: Reusable UI components (like `MoodGraph`).
- `src/pages/`: Main application views (`Dashboard`, `WelcomePage`, `Wellness`, etc.).
- `src/store.js`: Centralized state management.
- `index.html`: The main HTML entry point.

## Contributing
Feel free to open issues or submit pull requests if you'd like to improve MindNest!

## License
[MIT License](LICENSE)
