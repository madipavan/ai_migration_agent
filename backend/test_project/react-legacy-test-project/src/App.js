import React,{Component} from 'react';
import {BrowserRouter as Router} from 'react-router-dom';
import Header from './components/Header';
class App extends Component{
 render(){
  return <Router><Header/><h1>Legacy React 16 App</h1></Router>;
 }
}
export default App;
