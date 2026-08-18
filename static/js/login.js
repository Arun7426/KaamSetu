// ===============================
// Password Show / Hide
// ===============================

const password = document.getElementById("password");

const togglePassword = document.getElementById("togglePassword");

if (togglePassword && password) {

    togglePassword.addEventListener("click", function () {

        if (password.type === "password") {

            password.type = "text";

            this.innerHTML =
                '<i class="fa-solid fa-eye-slash"></i>';

        }

        else {

            password.type = "password";

            this.innerHTML =
                '<i class="fa-solid fa-eye"></i>';

        }

    });

}



// ===============================
// Role Tabs
// ===============================

const customerTab = document.getElementById("customerTab");

const workerTab = document.getElementById("workerTab");

const selectedRole = document.getElementById("selectedRole");

const heading = document.querySelector(".login-heading");

const subtitle = document.querySelector(".subtitle");



// ===============================
// Customer Tab
// ===============================

if (customerTab) {

    customerTab.addEventListener("click", function () {

        customerTab.classList.add("active");

        workerTab.classList.remove("active");


        if (selectedRole) {

            selectedRole.value = "customer";

        }


        heading.innerHTML =
            '<span class="blue">Kaam</span><span class="orange">Setu</span> Customer Login';

        subtitle.innerHTML =
            "अपने Customer अकाउंट में लॉगिन करें";

    });

}



// ===============================
// Worker Tab
// ===============================

if (workerTab) {

    workerTab.addEventListener("click", function () {

        workerTab.classList.add("active");

        customerTab.classList.remove("active");


        if (selectedRole) {

            selectedRole.value = "worker";

        }


        heading.innerHTML =
            '<span class="blue">Kaam</span><span class="orange">Setu</span> Worker Login';

        subtitle.innerHTML =
            "अपने Worker अकाउंट में लॉगिन करें";

    });

}