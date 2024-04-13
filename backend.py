from flask import Flask, jsonify, request, render_template
import yfinance as yf
import pandas as pd
from datetime import datetime
import webbrowser
import threading

app = Flask(__name__)

def open_browser():
    webbrowser.open('http://127.0.0.1:5000')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stock_data')
def stock_data():
    ticker = request.args.get('ticker')
    if not ticker:
        return jsonify({'error': 'No ticker provided'}), 400

    # 현재 날짜를 동적으로 가져오기
    end_date = datetime.now().strftime('%Y-%m-%d')

    try:
        # 데이터 다운로드 (2023년 6월 1일부터 현재까지)
        data = yf.download(ticker, start="2023-06-01", end=end_date)
        data.reset_index(inplace=True)
        data['Date'] = pd.to_datetime(data['Date']).dt.strftime('%Y-%m-%d')  # 날짜에서 시간 제거
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        
        data['Signal'] = 0
        data.loc[data['SMA_20'] > data['SMA_50'], 'Signal'] = 1
        data.loc[data['SMA_20'] < data['SMA_50'], 'Signal'] = -1
        data['Position'] = data['Signal'].diff()

        data['Buy_Price'] = None
        data['Sell_Price'] = None
        data.loc[data['Position'] == 2, 'Buy_Price'] = data['Close']
        data.loc[data['Position'] == -2, 'Sell_Price'] = data['Close']
        trades = data.dropna(subset=['Buy_Price', 'Sell_Price'])
        trades['Profit'] = trades['Sell_Price'].shift(-1) - trades['Buy_Price']

        total_profit = trades['Profit'].sum()
        investment_result = 'Profitable' if total_profit > 0 else 'Not Profitable'
        
        return jsonify({
            'data': data[['Date', 'Close', 'SMA_20', 'SMA_50', 'Signal']].tail(30).to_dict(orient='records'),  # 최근 30일 데이터 반환
            'investment_result': investment_result,
            'total_profit': total_profit
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    threading.Thread(target=open_browser).start()
    app.run(debug=True)
