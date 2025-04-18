import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { io } from 'socket.io-client';
import Webcam from 'react-webcam';

const App = () => {
  const [name, setName] = useState('');
  const [images, setImages] = useState([]);
  const [isWebcamOn, setWebcamOn] = useState(false);
  const [logs, setLogs] = useState([]);
  const [recognitionData, setRecognitionData] = useState([]);

  useEffect(() => {
    // Fetch unique recognition data initially
    const fetchLogs = async () => {
      try {
        const response = await axios.get('http://localhost:5000/log');
        setLogs(response.data.logs.split('\n').filter(log => log !== ""));
      } catch (error) {
        console.error('Error fetching logs:', error);
      }
    };
    fetchLogs();
    const fetchRecognitionData = async () => {
      try {
        const response = await axios.get('http://localhost:5000/recognition_data');
        setRecognitionData(response.data.data);
      } catch (error) {
        console.error('Error fetching recognition data:', error);
      }
    };

    fetchRecognitionData();

    // Set up socket connection for real-time updates
    const socket = io('http://localhost:5000');
    socket.on('webcam_update', (data) => {
      fetchLogs();
      fetchRecognitionData(); // Update recognition data in real-time
    });

    return () => {
      socket.disconnect(); // Disconnect when the component unmounts
    };
  }, []);

  const handleFileChange = (event) => {
    setImages([...event.target.files]);
  };

  const handleNameChange = (event) => {
    setName(event.target.value);
  };

  const handleUpload = async () => {
    if (!name || images.length === 0) {
      alert('Please provide a name and select at least one image.');
      return;
    }

    const formData = new FormData();
    formData.append('name', name);
    images.forEach((image) => formData.append('images', image));

    try {
      const response = await axios.post('http://localhost:5000/uploadimages', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      alert(response.data.message);
    } catch (error) {
      console.error('Error uploading images:', error);
      alert('Failed to upload images. Please try again.');
    }
  };

  const toggleWebcam = async () => {
    const newLog = isWebcamOn ? 'Webcam turned off' : 'Webcam turned on';
    setLogs((prevLogs) => [...prevLogs, newLog]); // Add a new log entry
    setWebcamOn((prev) => !prev);
    if (!isWebcamOn) {
      await axios.post('http://localhost:5000/start_webcam'); // Start webcam when button is pressed
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Identity Access Management</h1>
      </header>

      <main>
        <section>
          <h2>Add a New Person</h2>
          <input type="text" placeholder="Enter person's name" value={name} onChange={handleNameChange} />
          <input type="file" multiple accept="image/*" onChange={handleFileChange} />
          <button onClick={handleUpload}>Upload Photos</button>
        </section>

        <section>
          <h2>Webcam Access</h2>
          <button onClick={toggleWebcam}>{isWebcamOn ? 'Turn Off Webcam' : 'Turn On Webcam'}</button>
          {isWebcamOn && <Webcam className="webcam" />}
        </section>

        <section>
          <h2>Recognition Data</h2>
          <table border="1">
            <thead>
              <tr>
                <th>Name</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {recognitionData.map((entry, index) => (
                <tr key={index}>
                  <td>{entry.name}</td>
                  <td>{entry.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        <section>
          <h2>Logs</h2>
          <ul>
            {logs.map((log, index) => (
              <li key={index}>{log}</li>
            ))}
          </ul>
        </section>
      </main>
    </div>
  );
};

export default App;
