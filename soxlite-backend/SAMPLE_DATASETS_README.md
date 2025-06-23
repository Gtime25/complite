# CompLite Sample Datasets for PDF Testing

This directory contains comprehensive sample datasets designed to test all the enhanced PDF generation features in CompLite.

## 📊 SOX Dataset: `complex_sox_sample.csv`

### **Dataset Overview**
- **30 controls** across various business areas
- **Multiple risk levels**: Critical, High, Medium, Low
- **Various frequencies**: Monthly, Quarterly, Annual, Weekly
- **Mixed results**: Pass/Fail combinations
- **Different due dates**: Past, present, and future dates

### **Features This Tests**

#### 1. **Executive Summary Bullet Points**
- Total controls: 30
- Failed controls: 8 (26.7%)
- Overdue controls: 12 (40%)
- Missing owners: 0 (0%)
- Compliance score: ~33.3%

#### 2. **Compliance Score Chart**
- Visual breakdown of Passed/Failed/Overdue/Missing Owner percentages
- Color-coded bars with percentage labels

#### 3. **Risk vs Frequency Heatmap**
- Distribution across Risk Rating (Critical, High, Medium, Low)
- Test Frequency (Monthly, Quarterly, Annual, Weekly)
- Color intensity shows number of controls in each combination

#### 4. **Control Deep Dives**
- **Critical Controls**: 4 controls (Inventory, Revenue Recognition, IT Security, Financial Reporting, etc.)
- **Failed Controls**: 8 controls with specific recommendations
- **Overdue Controls**: 12 controls past due date

#### 5. **Benchmark Insights**
- AI comparison to typical SOX compliance benchmarks
- Industry-specific insights

#### 6. **Time Series Chart**
- Overdue controls grouped by due month
- Shows temporal patterns in compliance issues

#### 7. **Themed Recommendations**
- **Governance**: Board oversight, compliance monitoring
- **Financial Controls**: Revenue recognition, inventory, cash management
- **Operational**: IT security, vendor management, payroll
- **Technology**: System access, data backup, change management

---

## 🌱 ESG Dataset: `complex_esg_sample.csv`

### **Dataset Overview**
- **40 ESG metrics** across Environmental, Social, and Governance pillars
- **Various thresholds and values** for performance comparison
- **Mixed statuses**: Pass/Fail combinations
- **Different priorities**: Critical, High, Medium
- **Multiple categories**: Emissions, Energy, Waste, Workplace, etc.

### **Features This Tests**

#### 1. **Executive Summary Bullet Points**
- Total metrics: 40
- Failed metrics: 24 (60%)
- Overdue metrics: 15 (37.5%)
- Missing owners: 0 (0%)
- Compliance score: ~2.5%

#### 2. **Compliance Score Chart**
- Visual breakdown of ESG performance
- Shows environmental, social, and governance performance

#### 3. **Control Deep Dives**
- **Failed ESG Metrics**: 24 metrics with specific recommendations
- **Critical Priority**: 12 critical ESG factors
- **Overdue Metrics**: 15 metrics past due date

#### 4. **Benchmark Insights**
- AI comparison to typical ESG compliance benchmarks
- Industry-specific ESG insights

#### 5. **Time Series Chart**
- Overdue ESG metrics grouped by due month
- Shows temporal patterns in ESG compliance

#### 6. **Themed Recommendations**
- **Environmental**: Carbon emissions, energy efficiency, waste reduction, water usage
- **Social**: Employee satisfaction, diversity, community investment, workplace safety
- **Governance**: Board independence, ethics training, data privacy, cybersecurity

---

## 🧪 **Testing Scenarios**

### **SOX Testing**
1. **Upload** `complex_sox_sample.csv` in SOX mode
2. **Ask AI**: "Generate a comprehensive SOX compliance report"
3. **Check**: "Generate PDF report"
4. **Expected Results**:
   - Executive summary with bullet points
   - Compliance score chart (~33.3%)
   - Risk vs Frequency heatmap
   - 10+ control deep dives
   - Benchmark insights
   - Time series chart for overdue controls
   - Themed recommendations

### **ESG Testing**
1. **Upload** `complex_esg_sample.csv` in ESG mode
2. **Ask AI**: "Generate a comprehensive ESG compliance report"
3. **Check**: "Generate PDF report"
4. **Expected Results**:
   - Executive summary with bullet points
   - Compliance score chart (~2.5%)
   - 10+ ESG metric deep dives
   - Benchmark insights
   - Time series chart for overdue metrics
   - Themed recommendations by ESG pillar

---

## 📈 **Key Testing Features**

### **Anomaly Detection**
- **SOX**: Low-risk controls with failed results, high-risk with rare frequencies
- **ESG**: Critical factors with failed status, metrics below threshold

### **Alert Generation**
- **SOX**: High/critical risk controls with failed results, overdue controls
- **ESG**: Critical ESG factors with failed status, overdue metrics

### **Dashboard Metrics**
- **SOX**: High risk (8), Failed (8), Overdue (12)
- **ESG**: Critical (12), Failed (24), Overdue (15)

### **AI Recommendations**
- **SOX**: Governance, Financial, Operational, Technology themes
- **ESG**: Environmental, Social, Governance themes

---

## 🚀 **Usage Instructions**

1. **Start the backend**: `uvicorn main:app --reload`
2. **Start the frontend**: `npm start` (in frontend directory)
3. **Navigate to**: `http://localhost:3000`
4. **Select mode**: SOX or ESG
5. **Upload dataset**: Choose the appropriate CSV file
6. **Generate report**: Ask AI with PDF generation enabled

These datasets will provide comprehensive testing of all enhanced PDF generation features and demonstrate the full capabilities of the CompLite system! 