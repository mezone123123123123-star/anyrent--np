const openCameraButton = document.getElementById('open-camera-button');
const captureSelfieButton = document.getElementById('capture-selfie-button');
const stopCameraButton = document.getElementById('stop-camera-button');
const video = document.getElementById('webcam-video');
const selfieInput = document.getElementById('selfie');
const selfiePreview = document.getElementById('selfie-preview');
const cameraUnsupported = document.getElementById('camera-unsupported');

captureSelfieButton.disabled = true;
openCameraButton.disabled = false;

let stream = null;

function showElement(el) {
  if (el) {
    el.classList.remove('hidden');
    el.hidden = false;
  }
}

function hideElement(el) {
  if (el) {
    el.classList.add('hidden');
    el.hidden = true;
  }
}

function dataURLToBlob(dataUrl) {
  const [header, base64String] = dataUrl.split(',');
  const mime = header.match(/:(.*?);/)[1];
  const binary = atob(base64String);
  const array = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    array[i] = binary.charCodeAt(i);
  }
  return new Blob([array], { type: mime });
}

function stopStream() {
  if (!stream) return;
  stream.getTracks().forEach(track => track.stop());
  stream = null;
  hideElement(video);
  hideElement(stopCameraButton);
  hideElement(captureSelfieButton);
}

function captureSelfie() {
  if (!video || !stream) {
    cameraUnsupported.textContent = 'Camera is not active. Open the camera first.';
    showElement(cameraUnsupported);
    return;
  }

  const maxDimension = 640;
  const naturalWidth = video.videoWidth || maxDimension;
  const naturalHeight = video.videoHeight || maxDimension;
  const scale = Math.min(maxDimension / naturalWidth, maxDimension / naturalHeight, 1);
  const width = Math.round(naturalWidth * scale);
  const height = Math.round(naturalHeight * scale);

  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext('2d');
  context.drawImage(video, 0, 0, width, height);
  const dataUrl = canvas.toDataURL('image/jpeg', 0.75);
  selfiePreview.src = dataUrl;
  showElement(selfiePreview);

  const blob = dataURLToBlob(dataUrl);
  const file = new File([blob], 'selfie.jpg', { type: 'image/jpeg' });
  const dataTransfer = new DataTransfer();
  dataTransfer.items.add(file);
  selfieInput.files = dataTransfer.files;
}

openCameraButton.addEventListener('click', async () => {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    cameraUnsupported.textContent = 'Camera is not supported by this browser.';
    showElement(cameraUnsupported);
    return;
  }

  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
    video.muted = true;
    video.playsInline = true;
    await video.play();

    showElement(video);
    showElement(stopCameraButton);
    hideElement(cameraUnsupported);

    function enableCapture() {
      showElement(captureSelfieButton);
      captureSelfieButton.disabled = false;
    }

    if (video.readyState >= 1) {
      enableCapture();
    } else {
      video.addEventListener('loadedmetadata', enableCapture, { once: true });
    }
  } catch (error) {
    cameraUnsupported.textContent = 'Unable to open camera. Check your browser permissions.';
    showElement(cameraUnsupported);
  }
});

captureSelfieButton.addEventListener('click', captureSelfie);
stopCameraButton.addEventListener('click', () => {
  stopStream();
});

selfieInput.addEventListener('change', () => {
  if (selfieInput.files && selfieInput.files[0]) {
    const reader = new FileReader();
    reader.onload = () => {
      selfiePreview.src = reader.result;
      showElement(selfiePreview);
      stopStream();
    };
    reader.readAsDataURL(selfieInput.files[0]);
  }
});

window.addEventListener('beforeunload', stopStream);
