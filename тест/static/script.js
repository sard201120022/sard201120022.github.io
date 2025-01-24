const lenis = new Lenis({
	autoRaf: true,
});

function filterCards() {
	const searchInput = document.getElementById("cards_search").value.toLowerCase();
	const cards = document.querySelectorAll(".card");

	cards.forEach((card) => {
		const botName = card.querySelector(".card_bot_name").textContent.toLowerCase();
		if (botName.includes(searchInput)) {
			card.style.display = "flex";
		} else {
			card.style.display = "none";
		}
	});
}
