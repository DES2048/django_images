export default class {
    constructor() {
        this.imageContainer = document.getElementById("imageContainer");

    }
    drawImage(imageInfo) {

        if(document.querySelector('#imageContainer p.error-message')) {
            this.imageContainer.innerHTML = "";
        }

        this.drawImageInfo(imageInfo);

        let imgElem = document.getElementById("image");
        if (!imgElem) {
            imgElem = document.createElement('img');
            imgElem.id = 'image';
            imgElem.className= "responsive";
        }
        imgElem.src = imageInfo.image.url;
        this.imageContainer.appendChild(imgElem);

    }
    drawImageInfo(data) {
        let imageNameCont = document.getElementById("imageName");
        
        if(!imageNameCont) {
            imageNameCont = document.createElement('div');
            imageNameCont.id = "imageName";
            
            this.imageContainer.appendChild(imageNameCont);
        }
        imageNameCont.innerHTML = `(${data.index+1}/${data.count}) ${data.image.name}`;
    }
    drawError(message) {
        this.imageContainer.innerHTML = "";
    
        const msgElement = document.createElement("p");
        msgElement.innerHTML = message;
        msgElement.className = "error-message";
        imageContainer.append(msgElement);
    }
}