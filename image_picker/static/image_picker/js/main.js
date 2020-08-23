// api
const api = {
    endpoints: {
        settings: "/settings/",
        galleries: "/galleries/",
        randomUrl: "/get-random-image-url/",
        deleteImage: '/delete-image/',
    },
    getGalleries () {
        return fetch(this.endpoints["galleries"])
            .then(response => response.json());
    },
    getSettings () {
        return fetch(this.endpoints['settings'])
            .then(response => response.json());
    },
    saveSettings (settings) {
        return fetch(this.endpoints["settings"], {
            method: 'POST',
            body: JSON.stringify(settings)
        })
    },
    getRandomImageUrl () {
        return fetch(this.endpoints.randomUrl)
            .then(response => response.json())
            .then(data => {
                if (data.status === "ok") {
                    return data.url;
                } else {
                    return new Promise(
                        (resolve, reject) => reject(new Error(data.message)))
                }
            });
    },
    deleteImage(url) {
        return fetch(this.endpoints.deleteImage + url + "/", {
            method: "POST"
        })
    }
}

// app
const app = {
	api,
	data: {
		galleries: [],
		settings: {},
		currentImage: ""
	},
	getGalleries() {
		return this.api.getGalleries()
			.then(data => {
				this.data.galleries = data;
				return data
			})
	},
	getSettings() {
		return this.api.getSettings()
			.then(data => {
				this.data.settings = data;
				return data;	
			})
	},
	saveSettings(settings) {
		return this.api.saveSettings(settings)
			.then(response => {
				if(response.ok) {
					this.data.settings = settings;
					return True
				}
				return false
			})
	},
	deleteImage() {
		this.api.deleteImage(this.data.currentImage)
		.then(response => {
			if (response.ok) {
				this.redraw();
			}
		})
	},
	showImage(url) {
    	const image = document.getElementById("image");
    	image.src = "/get-image/" + this.data.settings.selected_gallery + "/" + url;
	},
	drawErrorContainer(message) {
    	const imageContainer = document.getElementById("imageContainer");
    	imageContainer.innerHTML = ""

    	const msgElement = document.createElement("p");
    	msgElement.innerHTML = message;
    	msgElement.className = "error-message";
    	imageContainer.append(msgElement);
	},
	redraw() {
    	this.api.getRandomImageUrl().then(url => {
        this.data.currentImage = url;
        const imgNameDiv = document.getElementById("imageName");
        imgNameDiv.innerHTML = url;

        this.showImage(url);
    })
        .catch(error => {
            this.drawErrorContainer(error.message);
        });
	},
	start() {
		this.getSettings().then(data => this.redraw())
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

    Promise.all([app.getGalleries(), app.getSettings()])
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
    app.saveSettings(settings)
        .catch(error => console.log(error.message))
        .finally(()=>closeSidenav());
})

// images

const rnd = document.getElementById("random");
rnd.addEventListener('click', function () {
    app.redraw();
});


const deleteButton = document.getElementById("delete");
deleteButton.addEventListener("click", () => {
    app.deleteImage(api.data.currentUrl);
});

app.start();