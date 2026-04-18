# 🚨 Fraud Detection System

## 📌 Overview

This project is an **AI-based anomaly detection system** designed to identify unusual patterns in data such as fraudulent transactions, abnormal user behavior, or outliers in datasets.

It uses multiple machine learning techniques to improve detection accuracy and provide flexibility across different types of datasets.

---

## 🎯 Objectives

* Detect anomalies in transaction or behavioral data
* Compare multiple anomaly detection algorithms
* Perform feature engineering for better model performance
* Provide a simple and structured system for real-world use

---

## 🧠 Algorithms Used

### 1. Isolation Forest

* Efficient for large datasets
* Detects anomalies by isolating data points
* Works well for high-dimensional data

### 2. One-Class SVM

* Learns the normal data pattern
* Detects deviations from normal behavior
* Suitable for complex data distributions

### 3. Statistical Methods

* **Z-Score**: Identifies values far from the mean
* **IQR (Interquartile Range)**: Detects outliers using quartiles

---

## ⚙️ Features

* Multiple anomaly detection techniques
* Feature engineering (time-based, categorical encoding)
* Log transformation for skewed data
* User-level anomaly detection
* CSV file upload support
* Organized project structure

---

## 🏗️ Project Structure

```
anomaly-detector/
│
├── app/
│   ├── models/          # ML algorithms
│   ├── preprocessing/   # Data cleaning & feature engineering
│   ├── utils/           # Helper functions
│
├── datasets/            # Sample datasets
├── static/uploads/      # Uploaded files
├── run.py               # Main application file
├── requirements.txt     # Dependencies
└── README.md            # Project documentation
```

---

## 📊 Dataset

The system works with transaction-based datasets containing features such as:

* Transaction amount
* Timestamp
* User ID
* Location
* Category

---

## ▶️ How to Run

### 1. Install Dependencies

```
pip install -r requirements.txt
```

### 2. Run the Application

```
python run.py
```

### 3. Upload Dataset

* Upload a CSV file
* The system will process and detect anomalies

---

## 📈 Output

* Identifies anomalous transactions
* Labels data as normal or anomaly
* Provides processed dataset with results

---

## 🔍 Use Cases

* Fraud detection in banking systems
* E-commerce transaction monitoring
* Network intrusion detection
* Behavioral analysis systems

---

## 🚀 Future Improvements

* Real-time anomaly detection using APIs
* Interactive dashboard with visualizations
* Deep learning-based models
* Integration with cloud platforms

---

## 👨‍💻 Author

**Sahal C**
BCA (AI, ML & Robotics) Student

---

## 📌 Conclusion

This project demonstrates how machine learning can be used to detect anomalies effectively. By combining multiple algorithms and preprocessing techniques, the system provides a flexible and scalable solution for real-world problems.

---
