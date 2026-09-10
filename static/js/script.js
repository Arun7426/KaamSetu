const slider = document.querySelector(".worker-slider");
const nextBtn = document.querySelector(".slider-next");
const prevBtn = document.querySelector(".slider-prev");

if (slider && nextBtn && prevBtn) {

    const cards = Array.from(
        slider.querySelectorAll(".worker-card")
    );

    let currentIndex = 0;

    function goToCard(index) {

        if (!cards.length) {
            return;
        }

        currentIndex = Math.max(
            0,
            Math.min(index, cards.length - 1)
        );

        const targetCard = cards[currentIndex];

        slider.scrollTo({
            left: targetCard.offsetLeft - slider.offsetLeft,
            behavior: "smooth"
        });
    }


    nextBtn.addEventListener("click", () => {

        if (currentIndex < cards.length - 1) {
            goToCard(currentIndex + 1);
        }

    });


    prevBtn.addEventListener("click", () => {

        if (currentIndex > 0) {
            goToCard(currentIndex - 1);
        }

    });


    /*
     * Keep currentIndex synchronized when
     * the user manually swipes/scrolls.
     */
    let scrollTimer;

    slider.addEventListener("scroll", () => {

        clearTimeout(scrollTimer);

        scrollTimer = setTimeout(() => {

            if (!cards.length) {
                return;
            }

            let closestIndex = 0;
            let closestDistance = Infinity;

            cards.forEach((card, index) => {

                const distance = Math.abs(
                    card.offsetLeft - slider.scrollLeft
                );

                if (distance < closestDistance) {
                    closestDistance = distance;
                    closestIndex = index;
                }

            });

            currentIndex = closestIndex;

        }, 100);

    });

}