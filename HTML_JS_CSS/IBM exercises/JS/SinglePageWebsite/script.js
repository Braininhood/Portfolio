function addRecommendation() {
  let recommendationText = document.getElementById("new_recommendation").value;

  if (recommendationText.trim() === "") return;

  let newRecommendation = document.createElement("div");
  newRecommendation.className = "recommendation";
  newRecommendation.innerHTML = `<span>&#8220;</span>${recommendationText}<span>&#8221;</span>`;

  document.getElementById("all_recommendations").appendChild(newRecommendation);
  document.getElementById("new_recommendation").value = "";

  showPopup(true);
}

function showPopup(bool) {
  let popup = document.getElementById("popup");
  popup.style.visibility = bool ? "visible" : "hidden";
}
