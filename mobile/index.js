// Polyfill must be first
import './src/polyfills/importMeta';

import { registerRootComponent } from 'expo';
import App from './App';

registerRootComponent(App);
