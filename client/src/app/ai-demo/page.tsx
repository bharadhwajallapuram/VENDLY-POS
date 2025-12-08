"use client";
// Moved the AI demo page implementation here for Next.js route compatibility
import React, { useState } from 'react';
import {
	forecastSales,
	detectAnomalies,
	recommendProducts,
	suggestPrice,
	askAnalytics,
	voiceCommand,
} from '../../lib/aiApi';

export default function AiDemoPage() {
	const [forecastResult, setForecastResult] = useState<any>(null);
	const [forecastError, setForecastError] = useState<string | null>(null);
	const [anomalyResult, setAnomalyResult] = useState<any>(null);
	const [anomalyError, setAnomalyError] = useState<string | null>(null);
	const [recommendResult, setRecommendResult] = useState<any>(null);
	const [recommendError, setRecommendError] = useState<string | null>(null);
	const [priceResult, setPriceResult] = useState<any>(null);
	const [priceError, setPriceError] = useState<string | null>(null);
	const [askResult, setAskResult] = useState<any>(null);
	const [askError, setAskError] = useState<string | null>(null);
	const [voiceResult, setVoiceResult] = useState<any>(null);
	const [voiceError, setVoiceError] = useState<string | null>(null);

	const handleForecast = async () => {
		setForecastError(null);
		try {
			const res = await forecastSales({ product_id: 1, days: 7 });
			setForecastResult(res);
		} catch (err: any) {
			setForecastResult(null);
			setForecastError(err.message || 'Error');
		}
	};
	const handleAnomaly = async () => {
		setAnomalyError(null);
		try {
			const res = await detectAnomalies({
				sales_data: [
					{ date: '2025-12-01', sales: 100 },
					{ date: '2025-12-02', sales: 120 },
					{ date: '2025-12-03', sales: 500 },
					{ date: '2025-12-04', sales: 110 },
				],
				threshold: 2.0,
			});
			setAnomalyResult(res);
		} catch (err: any) {
			setAnomalyResult(null);
			setAnomalyError(err.message || 'Error');
		}
	};
	const handleRecommend = async () => {
		setRecommendError(null);
		try {
			const res = await recommendProducts({ customer_id: 1, n: 3 });
			setRecommendResult(res);
		} catch (err: any) {
			setRecommendResult(null);
			setRecommendError(err.message || 'Error');
		}
	};
	const handlePrice = async () => {
		setPriceError(null);
		try {
			const res = await suggestPrice({ product_id: 1 });
			setPriceResult(res);
		} catch (err: any) {
			setPriceResult(null);
			setPriceError(err.message || 'Error');
		}
	};
	const handleAsk = async () => {
		setAskError(null);
		try {
			const res = await askAnalytics({ question: 'Who was the top seller last month?' });
			setAskResult(res);
		} catch (err: any) {
			setAskResult(null);
			setAskError(err.message || 'Error');
		}
	};
	const handleVoice = async () => {
		setVoiceError(null);
		try {
			const res = await voiceCommand({ command: 'Sell 2 units of Product X' });
			setVoiceResult(res);
		} catch (err: any) {
			setVoiceResult(null);
			setVoiceError(err.message || 'Error');
		}
	};

	return (
		<div style={{ padding: 24 }}>
			<h1>Vendly AI Demo</h1>
			<button onClick={handleForecast}>Test Forecast</button>
			{forecastError ? <div style={{color:'red'}}>{forecastError}</div> : <pre>{forecastResult ? JSON.stringify(forecastResult, null, 2) : 'No result yet.'}</pre>}
			<button onClick={handleAnomaly}>Test Anomaly</button>
			{anomalyError ? <div style={{color:'red'}}>{anomalyError}</div> : <pre>{anomalyResult ? JSON.stringify(anomalyResult, null, 2) : 'No result yet.'}</pre>}
			<button onClick={handleRecommend}>Test Recommend</button>
			{recommendError ? <div style={{color:'red'}}>{recommendError}</div> : <pre>{recommendResult ? JSON.stringify(recommendResult, null, 2) : 'No result yet.'}</pre>}
			<button onClick={handlePrice}>Test Price Suggest</button>
			{priceError ? <div style={{color:'red'}}>{priceError}</div> : <pre>{priceResult ? JSON.stringify(priceResult, null, 2) : 'No result yet.'}</pre>}
			<button onClick={handleAsk}>Test Ask</button>
			{askError ? <div style={{color:'red'}}>{askError}</div> : <pre>{askResult ? JSON.stringify(askResult, null, 2) : 'No result yet.'}</pre>}
			<button onClick={handleVoice}>Test Voice</button>
			{voiceError ? <div style={{color:'red'}}>{voiceError}</div> : <pre>{voiceResult ? JSON.stringify(voiceResult, null, 2) : 'No result yet.'}</pre>}
		</div>
	);
}
