import React, { useEffect, useState } from "react";
import axios from "../services/api";
import "../styles/IAMManager.css";

const IAMManager = () => {
    const [users, setUsers] = useState([]);
    const [form, setForm] = useState({
        name: "",
        employee_id: "",
        securityLevel: "",
        department: "",
        role: "",
        email: "",
    });

    useEffect(() => {
        fetchUsersFromIPFS();
    }, []);

    const fetchUsersFromIPFS = async () => {
        try {
            const response = await axios.get("/employees");
            setUsers(response.data);
        } catch (error) {
            console.error("Error fetching employees from IPFS:", error);
        }
    };

    const validateForm = () => {
        const { name, employee_id, securityLevel, department, role, email } = form;
    
        if (!name || !employee_id || !securityLevel || !department || !role || !email) {
            alert("All fields are required.");
            return false;
        }
    
        if (!/^[a-zA-Z\s]+$/.test(name)) {
            alert("Name must contain only letters and spaces.");
            return false;
        }
    
        if (!/^[a-zA-Z0-9]+$/.test(employee_id)) {
            alert("Employee ID must be alphanumeric.");
            return false;
        }
    
        const securityLevelNum = Number(securityLevel);
        if (isNaN(securityLevelNum) || securityLevelNum < 1 || securityLevelNum > 6) {
            alert("Security Level must be between 1 and 6.");
            return false;
        }
    
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            alert("Please enter a valid email address.");
            return false;
        }
    
        return true;
    };
    

    const addUser = async () => {
        if (!validateForm()) return;
        try {
            const updatedForm = { ...form, securityLevel: Number(form.securityLevel) };

            await axios.post("/employees", updatedForm);
            setForm({ name: "", employee_id: "", securityLevel: "", department: "", role: "", email: "" });
            fetchUsersFromIPFS();
        } catch (error) {
            console.error("Error adding user:", error);
            if (error.response?.data?.error) {
                alert(error.response.data.error);
            }
        }
    };

    const deleteUser = async (employee_id) => {
        try {
            await axios.delete(`/employees/${employee_id}`);
            fetchUsersFromIPFS(); // Refresh the user list
        } catch (error) {
            console.error("Error deleting user:", error);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setForm({ ...form, [name]: value });
    };

    return (
        <div>
            <h2>IAM Management</h2>
            <form>
                <input
                    type="text"
                    name="name"
                    value={form.name}
                    onChange={handleChange}
                    placeholder="Employee Name"
                    required
                />
                <input
                    type="text"
                    name="employee_id"
                    value={form.employee_id}
                    onChange={handleChange}
                    placeholder="Employee ID"
                    required
                />
                <input
                    type="number"
                    name="securityLevel"
                    value={form.securityLevel}
                    onChange={handleChange}
                    placeholder="Security Level (1-6)"
                    min="1"
                    max="6"
                    required
                />
                <input
                    type="text"
                    name="department"
                    value={form.department}
                    onChange={handleChange}
                    placeholder="Department"
                    required
                />
                <input
                    type="text"
                    name="role"
                    value={form.role}
                    onChange={handleChange}
                    placeholder="Role"
                    required
                />
                <input
                    type="email"
                    name="email"
                    value={form.email}
                    onChange={handleChange}
                    placeholder="Email"
                    required
                />
                <button type="button" onClick={addUser}>
                    Add User
                </button>
            </form>
            <h3>Employee List</h3>
            <table border="1">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Employee ID</th>
                        <th>Security Level</th>
                        <th>Department</th>
                        <th>Role</th>
                        <th>Email</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {users.map((user, index) => (
                        <tr key={index}>
                            <td>{user.name}</td>
                            <td>{user.employee_id}</td>
                            <td>{user.securityLevel}</td>
                            <td>{user.department}</td>
                            <td>{user.role}</td>
                            <td>{user.email}</td>
                            <td>
                                <button onClick={() => deleteUser(user.employee_id)}>Delete</button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default IAMManager;
