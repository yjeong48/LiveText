import axios from 'axios';
import React,{Component} from 'react';

class App extends Component {
	state = {
	// Initially, no file is selected
	selectedFile: null,
	target_lang: ""
	};

	// After selecting file from pop up
	onFileChange = event => {
	this.setState({ selectedFile: event.target.files[0] });	
	};
	
	// After clicking the translate button)
	onFileUpload = () => {
	
	const formData = new FormData();
	formData.append(
		"file",
		this.state.selectedFile,
		this.state.selectedFile.name
	);
	
	// Details of the uploaded file
	console.log(this.state.selectedFile);
	
	// Request made to the backend api
	axios.post("http://localhost:5000", formData)
	.then(response => this.setState({ translated_text: response.data}))
	.catch(function (error) {
		console.log(error)
	})
	}
	
	//Display translated text
	translated = () => {
		return (
			<div>
				<p>Translated text: </p>
				<p>{this.state.translated_text}</p>
			</div>
		)
	}
	
	render() {
	return (
		<div style={{textAlign:"center"}}>
			<h1>
			OCR Personal Project
			</h1>
			<h3>
			Translate text from any image to Korean
			</h3>
			<div>
				<input type="file" onChange={this.onFileChange} />
				<button onClick={this.onFileUpload}>
				Translate!
				</button>
			</div>
		{this.translated()}
		</div>
	);
	}
}

export default App;


