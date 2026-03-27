import os
import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# Setup saving directory
SAVE_DIR = os.path.join(os.path.dirname(__file__), 'models', 'saved')
os.makedirs(SAVE_DIR, exist_ok=True)

NUM_SAMPLES = 5000

def generate_cc_data():
    """ Credit Card: velocity, foreignIp, hour vs normal """
    np.random.seed(42)
    # 0 = Normal, 1 = Fraud
    labels = np.random.choice([0, 1], size=NUM_SAMPLES, p=[0.7, 0.3])
    
    amount = []
    hour = []
    velocity = []
    newDevice = []
    foreignIp = []
    
    for y in labels:
        if y == 1:
            amount.append(np.random.randint(50000, 500000) if np.random.rand() < 0.8 else np.random.randint(100, 50000))
            hour.append(np.random.randint(1, 5) if np.random.rand() < 0.7 else np.random.randint(0, 23))
            velocity.append(np.random.randint(4, 20))
            newDevice.append(1 if np.random.rand() < 0.8 else 0)
            foreignIp.append(1 if np.random.rand() < 0.6 else 0)
        else:
            amount.append(np.random.randint(100, 30000))
            hour.append(np.random.randint(6, 22))
            velocity.append(np.random.randint(1, 4))
            newDevice.append(1 if np.random.rand() < 0.1 else 0)
            foreignIp.append(1 if np.random.rand() < 0.05 else 0)
            
    df = pd.DataFrame({
        'amount': amount, 'hour': hour, 'velocity': velocity,
        'newDevice': newDevice, 'foreignIp': foreignIp, 'is_fraud': labels
    })
    return df

def generate_ml_data():
    """ Money Laundering: amount, txnCount24h, crossBorder, shellCompany, structuring """
    np.random.seed(43)
    labels = np.random.choice([0, 1], size=NUM_SAMPLES, p=[0.8, 0.2])
    
    amount = []
    txnCount24h = []
    crossBorder = []
    shellCompany = []
    structuring = []
    accountAgeMonths = []
    
    for y in labels:
        if y == 1:
            amount.append(np.random.randint(200000, 990000))
            txnCount24h.append(np.random.randint(5, 50))
            crossBorder.append(1 if np.random.rand() < 0.6 else 0)
            shellCompany.append(1 if np.random.rand() < 0.7 else 0)
            structuring.append(1 if np.random.rand() < 0.8 else 0)
            accountAgeMonths.append(np.random.randint(1, 12))
        else:
            amount.append(np.random.randint(1000, 100000))
            txnCount24h.append(np.random.randint(1, 10))
            crossBorder.append(1 if np.random.rand() < 0.05 else 0)
            shellCompany.append(0)
            structuring.append(1 if np.random.rand() < 0.02 else 0)
            accountAgeMonths.append(np.random.randint(12, 120))
            
    df = pd.DataFrame({
        'amount': amount, 'txnCount24h': txnCount24h, 'crossBorder': crossBorder,
        'shellCompany': shellCompany, 'structuring': structuring,
        'accountAgeMonths': accountAgeMonths, 'is_fraud': labels
    })
    return df

def generate_ut_data():
    """ Unauthorized: hour, accountAgeMonths, newDevice, newBeneficiary, multipleOtpFail, credentialChange, geoMismatch """
    np.random.seed(44)
    labels = np.random.choice([0, 1], size=NUM_SAMPLES, p=[0.8, 0.2])
    
    # Init arrays
    amount, hour, accountAgeMonths, newDevice, newBeneficiary = [], [], [], [], []
    multipleOtpFail, credentialChange, geoMismatch = [], [], []
    
    for y in labels:
        if y == 1:
            amount.append(np.random.randint(50000, 500000))
            hour.append(np.random.randint(0, 5) if np.random.rand() < 0.5 else np.random.randint(0, 23))
            accountAgeMonths.append(np.random.randint(1, 24))
            newDevice.append(1)
            newBeneficiary.append(1 if np.random.rand() < 0.9 else 0)
            multipleOtpFail.append(1 if np.random.rand() < 0.6 else 0)
            credentialChange.append(1 if np.random.rand() < 0.5 else 0)
            geoMismatch.append(1 if np.random.rand() < 0.7 else 0)
        else:
            amount.append(np.random.randint(100, 20000))
            hour.append(np.random.randint(6, 22))
            accountAgeMonths.append(np.random.randint(24, 120))
            newDevice.append(1 if np.random.rand() < 0.1 else 0)
            newBeneficiary.append(1 if np.random.rand() < 0.2 else 0)
            multipleOtpFail.append(1 if np.random.rand() < 0.05 else 0)
            credentialChange.append(0)
            geoMismatch.append(0)
            
    df = pd.DataFrame({
        'amount': amount, 'hour': hour, 'accountAgeMonths': accountAgeMonths,
        'newDevice': newDevice, 'newBeneficiary': newBeneficiary,
        'multipleOtpFail': multipleOtpFail, 'credentialChange': credentialChange,
        'geoMismatch': geoMismatch, 'is_fraud': labels
    })
    return df

def generate_ft_data():
    """ Fake Transaction: accountAgeMonths, merchantRisk, chargebackHistory, syntheticId, ghostMerchant, rapidCreditUtilisation, invoiceInflation """
    np.random.seed(45)
    labels = np.random.choice([0, 1], size=NUM_SAMPLES, p=[0.7, 0.3])
    
    amount, accountAgeMonths, merchantRisk, chargebackHistory = [], [], [], []
    syntheticId, ghostMerchant, rapidCreditUtilisation, invoiceInflation = [], [], [], []
    
    for y in labels:
        if y == 1:
            amount.append(np.random.randint(10000, 990000))
            accountAgeMonths.append(np.random.randint(1, 6))
            merchantRisk.append(np.random.uniform(0.6, 1.0))
            chargebackHistory.append(np.random.randint(3, 15))
            syntheticId.append(1 if np.random.rand() < 0.8 else 0)
            ghostMerchant.append(1 if np.random.rand() < 0.7 else 0)
            rapidCreditUtilisation.append(1 if np.random.rand() < 0.8 else 0)
            invoiceInflation.append(1 if np.random.rand() < 0.6 else 0)
        else:
            amount.append(np.random.randint(50, 10000))
            accountAgeMonths.append(np.random.randint(12, 120))
            merchantRisk.append(np.random.uniform(0.0, 0.3))
            chargebackHistory.append(0)
            syntheticId.append(0)
            ghostMerchant.append(0)
            rapidCreditUtilisation.append(1 if np.random.rand() < 0.05 else 0)
            invoiceInflation.append(0)
            
    df = pd.DataFrame({
        'amount': amount, 'accountAgeMonths': accountAgeMonths, 'merchantRisk': merchantRisk,
        'chargebackHistory': chargebackHistory, 'syntheticId': syntheticId,
        'ghostMerchant': ghostMerchant, 'rapidCreditUtilisation': rapidCreditUtilisation,
        'invoiceInflation': invoiceInflation, 'is_fraud': labels
    })
    return df

def generate_it_data():
    """ Identity Theft: amount, frequentPwdChange, fakeDocuments, creditPull """
    np.random.seed(46)
    labels = np.random.choice([0, 1], size=NUM_SAMPLES, p=[0.8, 0.2])
    
    amount, frequentPwdChange, fakeDocuments, creditPull = [], [], [], []
    
    for y in labels:
        if y == 1:
            amount.append(np.random.randint(200000, 990000))
            frequentPwdChange.append(1 if np.random.rand() < 0.8 else 0)
            fakeDocuments.append(1 if np.random.rand() < 0.7 else 0)
            creditPull.append(1 if np.random.rand() < 0.9 else 0)
        else:
            amount.append(np.random.randint(100, 20000))
            frequentPwdChange.append(1 if np.random.rand() < 0.05 else 0)
            fakeDocuments.append(0)
            creditPull.append(1 if np.random.rand() < 0.1 else 0)

    df = pd.DataFrame({
        'amount': amount, 'frequentPwdChange': frequentPwdChange,
        'fakeDocuments': fakeDocuments, 'creditPull': creditPull, 'is_fraud': labels
    })
    return df

def train_and_save(df, filename):
    X = df.drop('is_fraud', axis=1)
    y = df['is_fraud']
    
    clf = RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42)
    clf.fit(X, y)
    
    filepath = os.path.join(SAVE_DIR, filename)
    with open(filepath, 'wb') as f:
        pickle.dump(clf, f)
    print(f"✅ Trained and saved {filename} (Accuracy roughly: {clf.score(X,y):.2%}) - Features: {list(X.columns)}")

if __name__ == "__main__":
    print("Generating Synthetic Data and Training Models...")
    train_and_save(generate_cc_data(), 'cc_model.pkl')
    train_and_save(generate_ml_data(), 'ml_model.pkl')
    train_and_save(generate_ut_data(), 'ut_model.pkl')
    train_and_save(generate_ft_data(), 'ft_model.pkl')
    train_and_save(generate_it_data(), 'it_model.pkl')
    print("🎉 All Models Trained and Saved Successfully!")
