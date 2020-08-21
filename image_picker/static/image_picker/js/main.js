// api
const api = {
    endpoints: {
        settings: "/settings/",
        galleries: "/galleries/",
        randomUrl: "/get-random-image-url/",
        deleteImage: '/delete-image/',
    },
    data: {
        currentUrl: "",
        galleries: [],

    },
    getGalleries: function () {
        return fetch(this.endpoints["galleries"])
            .then(response => response.json());
    },
    getSettings: function () {
        return fetch(this.endpoints['settings'])
            .then(response => response.json());
    },
    saveSettings: function (settings) {
        return fetch(this.endpoints["settings"], {
            method: 'POST',
            body: JSON.stringify(settings)
        })
    },
    getRandomImageUrl: function () {
        return fetch(this.endpoints.randomUrl)
            .then(response => response.json())
            .then(data => {
                if (data.status === "ok") {
                    this.data.currentUrl = data.url;
                    return data.url;
                } else {
                    this.data.currentUrl = "";
                    return new Promise(
                        (resolve, reject) => reject(new Error(data.message)))
                }
            });
    },
    deleteImage(url) {
        return fetch(this.endpoints.deleteImage + api.data.currentUrl + "/", {
            method: "POST"
        })
    }
}

// side navigation
const sidenavOpen = document.getElementById("sidenavOpen");
const sidenavClose = document.getElementById("sidenavClose");
const sidenav = document.getElementById("sidenav");
const saveButton = document.getElementById("btnSave");

sidenavOpen.addEventListener("click", () => {
    sidenav.classList.add("sidenav-open");


    const gallsContainer = document.getElementsByClassName("galleries-container")[0];
    gallsContainer.innerHTML = "";

    Promise.all([api.getGalleries(), api.getSettings()])
        .then(results => {
            // draw galleries
            const galls = results[0];
            const settings = results[1];

            const selected_gallery = settings && settings.selected_gallery;
			const show_mode = settings && settings.show_mode;
			document.getElementById("showMode").value=show_mode
			
            galls.map((gallery) => {
                const elem = document.createElement("a");
                elem.innerHTML = gallery.title;
                elem.dataset.id = gallery.slug;
                elem.href = "javascript:void(0);";
                if (gallery.slug == selected_gallery) {
                    elem.classList.add("selected");
                    elem.dataset.active = "true";
                }

                elem.onclick = () => {
                    if (elem.classList.contains("selected")) {
                        return
                    }
                     const prevSelected =
                         document.querySelector(".galleries-container a.selected");
                    if(prevSelected) {
                        prevSelected.classList.remove("selected");
                    }
                    elem.classList.add("selected");
                }
                gallsContainer.append(elem);
            });
        });

});
function closeSidenav() {
	sidenav.classList.remove("sidenav-open");
}
sidenavClose.addEventListener("click", closeSidenav);

saveButton.addEventListener("click", () => {
    const settings = {
        show_mode: document.getElementById("showMode").value,
        selected_gallery: document.querySelector(".galleries-container a.selected").dataset.id
    }
    api.saveSettings(settings)
        .then(response => response.json())
        .catch(error => console.log(error.message));
        closeSidenav();
})

// images

function showImage(url) {
    const image = document.getElementById("image");
    image.src = "/get-image/" + url;
}

function drawErrorContainer(message) {
    const imageContainer = document.getElementById("imageContainer");
    imageContainer.innerHTML = ""

    const msgElement = document.createElement("p");
    msgElement.innerHTML = message;
    msgElement.className = "error-message";
    imageContainer.append(msgElement);
}

function redraw() {
    api.getRandomImageUrl().then(url => {
        const imgNameDiv = document.getElementById("imageName");
        imgNameDiv.innerHTML = url;

        showImage(url);
    })
        .catch(error => {
            drawErrorContainer(error.message);
        });
}

const rnd = document.getElementById("random");
rnd.addEventListener('click', function () {
    redraw();
});


const deleteButton = document.getElementById("delete");
deleteButton.addEventListener("click", () => {
    api.deleteImage(api.data.currentUrl).then(response => {
        if(response.ok) {
            redraw();
        }
    }).catch(error => {
        drawErrorContainer(error.message);
    })
});

redraw();