import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar";
import Home from "./pages/Home";
import CreatePipeline from "./pages/CreatePipeline";
import IAMPage from "./pages/IAMPage";
import Vision from "./pages/Vision";

function App() {
  return (
    <Router>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/create-pipeline" element={<CreatePipeline />} />
        <Route path="/iam" element={<IAMPage />} />
        <Route path="/vision" element={<Vision />} />
      </Routes>
    </Router>
  );
}

export default App;
