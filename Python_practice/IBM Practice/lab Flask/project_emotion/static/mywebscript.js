let RunSentimentAnalysis = () => {
    let textToAnalyze = document.getElementById("textToAnalyze").value;

    let xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4) {
            if (this.status == 200) {
                document.getElementById("system_response").innerHTML = this.responseText;
            } else if (this.status == 400) {
                try {
                    let errorResponse = JSON.parse(this.responseText);
                    document.getElementById("system_response").innerHTML = errorResponse.error;
                } catch (e) {
                    document.getElementById("system_response").innerHTML = "An error occurred. Please try again.";
                }
            } else {
                document.getElementById("system_response").innerHTML = "Unexpected error. Status code: " + this.status;
            }
        }
    };

    xhttp.open("GET", "emotionDetector?textToAnalyze=" + encodeURIComponent(textToAnalyze), true);
    xhttp.send();
};
