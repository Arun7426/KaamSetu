const slider = document.querySelector(".worker-slider");
const nextBtn = document.querySelector(".slider-next");
const prevBtn = document.querySelector(".slider-prev");

if (slider && nextBtn && prevBtn) {

    nextBtn.addEventListener("click", () => {
        slider.scrollBy({
            left: 320,
            behavior: "smooth"
        });
    });

    prevBtn.addEventListener("click", () => {
        slider.scrollBy({
            left: -320,
            behavior: "smooth"
        });
    });

}