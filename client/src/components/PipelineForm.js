import { Field, Form, Formik } from "formik";
import React, { useEffect, useState } from "react";
import * as Yup from "yup";
import axios from "../services/api";

const PipelineSchema = Yup.object().shape({
    pipelineName: Yup.string().required("Pipeline name is required"),
    employee_id: Yup.string().required("Employee ID is required"),
    file: Yup.mixed().required("A file is required"),
});

const PipelineForm = () => {
    const [pipelines, setPipelines] = useState([]);
    const [showDialog, setShowDialog] = useState(false);
    const [selectedPipeline, setSelectedPipeline] = useState(null);
    const [employeeId, setEmployeeId] = useState("");
    const [securityLevel, setSecurityLevel] = useState("");
    const [retrievedData, setRetrievedData] = useState(null);
    const [showDataDialog, setShowDataDialog] = useState(false);

    const fetchPipelines = async () => {
        try {
            const response = await axios.get("/pipelines");
            setPipelines(response.data);
        } catch (error) {
            console.error("Error fetching pipelines:", error);
        }
    };

    useEffect(() => {
        fetchPipelines();
    }, []);

    const handleSubmit = async (values) => {
        const formData = new FormData();
        formData.append("file", values.file);
        formData.append("pipeline_name", values.pipelineName);
        formData.append("employee_id", values.employee_id);
    
        try {
            const response = await axios.post("/upload", formData);
            alert("Pipeline created successfully: " + JSON.stringify(response.data));
            fetchPipelines();
        } catch (error) {
            const errorMsg = error.response?.data?.error || "An unexpected error occurred.";
            console.error("Error creating pipeline:", error);
            alert("Error creating pipeline: " + errorMsg);
        }
    };

    const handleRetrieve = async (pipeline) => {
        setSelectedPipeline(pipeline);
        setShowDialog(true);
    };

    const handleDialogClose = () => {
        setShowDialog(false);
        setSelectedPipeline(null);
        setEmployeeId("");
        setSecurityLevel("");
        setRetrievedData(null);
        setShowDataDialog(false);
    };

    const handleRetrieveFile = async () => {
        if (!employeeId || !securityLevel) {
            alert("Both Employee ID and Security Level are required.");
            return;
        }
    
        try {
            const response = await axios.post(`/retrieve`, {
                employee_id: employeeId,
                security_level: parseInt(securityLevel),
                record_id: selectedPipeline.record_id,
                ipfs_hash: selectedPipeline.ipfsHash,
            },
            { responseType: "blob" }      // <-- important!
            );
    
            if (response.data.data) {
                // If the response contains text data
                setRetrievedData(response.data.data);
                setShowDataDialog(true); // Show the data dialog
            } else {
                // If the response contains a file
                const blob = new Blob([response.data], { type: "application/octet-stream" });
                const url = URL.createObjectURL(blob);
                const link = document.createElement("a");
                link.href = url;
                link.download = "retrieved_file";
                link.click();
                URL.revokeObjectURL(url);
            }
            // Try to parse a filename out of the header:
            const disposition = response.headers["content-disposition"] || "";
            let fname = selectedPipeline.filename || "downloaded_file";
            const match = disposition.match(/filename="?(.+?)"?(;|$)/);
            if (match) fname = match[1];

            // Download the blob with correct name & type:
            const blob = new Blob([response.data], { type: response.data.type || selectedPipeline.mimetype });
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = fname;
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(url);
        } catch (error) {
            const errorMsg = error.response?.data?.error || "An unexpected error occurred.";
            alert("Error retrieving file: " + errorMsg);
        }
    };

    return (
        <div>
            <h2>Pipeline Form</h2>
            <Formik
                initialValues={{ pipelineName: "", employee_id: "", file: null }}
                validationSchema={PipelineSchema}
                onSubmit={handleSubmit}
            >
                {({ setFieldValue }) => (
                    <Form>
                        <label>Pipeline Name:</label>
                        <Field name="pipelineName" />
                        <label>Employee ID:</label>
                        <Field name="employee_id" />
                        <label>File:</label>
                        <input
                            name="file"
                            type="file"
                            onChange={(event) => {
                                setFieldValue("file", event.target.files[0]);
                            }}
                        />
                        <button type="submit">Create Pipeline</button>
                    </Form>
                )}
            </Formik>

            <h3>Created Pipelines</h3>
            <table border="1">
                <thead>
                    <tr>
                        <th>Serial Number</th>
                        <th>Pipeline Name</th>
                        <th>Employee ID</th>
                        <th>IPFS Hash</th>
                        <th>Retrieve</th>
                    </tr>
                </thead>
                <tbody>
                    {pipelines.map((pipeline) => (
                        <tr key={pipeline.record_id}>
                            <td>{pipeline.record_id}</td>
                            <td>{pipeline.pipelineName}</td>
                            <td>{pipeline.employee_id}</td>
                            <td>{pipeline.ipfsHash}</td>
                            <td>
                                <button onClick={() => handleRetrieve(pipeline)}>Retrieve File</button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>

            {showDialog && (
                <div className="dialog">
                    <h3>Retrieve File</h3>
                    <div>
                        <label>Employee ID:</label>
                        <input
                            type="text"
                            value={employeeId}
                            onChange={(e) => setEmployeeId(e.target.value)}
                            placeholder="Enter Employee ID"
                        />
                    </div>
                    <div>
                        <label>Security Level:</label>
                        <input
                            type="number"
                            value={securityLevel}
                            onChange={(e) => setSecurityLevel(e.target.value)}
                            placeholder="Enter Security Level"
                        />
                    </div>
                    <button onClick={handleRetrieveFile}>Retrieve</button>
                    <button onClick={handleDialogClose}>Cancel</button>
                </div>
            )}

            {showDataDialog && (
                <div className="retrievedDataDialog">
                    <h2>Retrieved Data</h2>
                    <pre>{retrievedData}</pre>
                    <button onClick={handleDialogClose}>Close</button>
                </div>
            )}
        </div>
    );
};

export default PipelineForm;
