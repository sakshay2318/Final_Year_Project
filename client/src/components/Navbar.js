import React from "react";
import { Link } from "react-router-dom";
import "../styles/Navbar.css"


const Navbar = () => {
    return (
        <nav>
            <ul>
                <li><Link to="/">Home</Link></li>
                <li><Link to="/create-pipeline">Create Pipeline</Link></li>
                <li><Link to="/iam">IAM</Link></li>
                <li><Link to="/vision">Vision</Link></li>
            </ul>
        </nav>
    );
};

export default Navbar;
