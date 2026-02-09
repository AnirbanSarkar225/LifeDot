// Custom Cursor Animation - Active Theory Style
class CursorAnimation {
  constructor() {
    this.cursor = null;
    this.cursorFollower = null;
    this.mouseX = window.innerWidth / 2;
    this.mouseY = window.innerHeight / 2;
    this.followerX = this.mouseX;
    this.followerY = this.mouseY;
    
    this.init();
  }
  
  init() {
    // Create cursor elements if they don't exist
    if (!document.querySelector('.cursor')) {
      this.cursor = document.createElement('div');
      this.cursor.className = 'cursor';
      document.body.appendChild(this.cursor);
    } else {
      this.cursor = document.querySelector('.cursor');
    }
    
    if (!document.querySelector('.cursor-follower')) {
      this.cursorFollower = document.createElement('div');
      this.cursorFollower.className = 'cursor-follower';
      document.body.appendChild(this.cursorFollower);
    } else {
      this.cursorFollower = document.querySelector('.cursor-follower');
    }
    
    // Mouse move event
    document.addEventListener('mousemove', (e) => {
      this.mouseX = e.clientX;
      this.mouseY = e.clientY;
      
      if (this.cursor) {
        this.cursor.style.left = this.mouseX + 'px';
        this.cursor.style.top = this.mouseY + 'px';
      }
    });
    
    // Start animation
    this.animate();
    
    // Add hover effects to interactive elements
    this.addHoverEffects();
  }
  
  animate() {
    this.followerX += (this.mouseX - this.followerX) * 0.1;
    this.followerY += (this.mouseY - this.followerY) * 0.1;
    
    if (this.cursorFollower) {
      this.cursorFollower.style.left = this.followerX + 'px';
      this.cursorFollower.style.top = this.followerY + 'px';
    }
    
    requestAnimationFrame(() => this.animate());
  }
  
  addHoverEffects() {
    const elements = document.querySelectorAll('a, button, input, textarea, .card, .btn');
    
    elements.forEach(el => {
      el.addEventListener('mouseenter', () => {
        if (this.cursor) {
          this.cursor.classList.add('hover');
        }
      });
      
      el.addEventListener('mouseleave', () => {
        if (this.cursor) {
          this.cursor.classList.remove('hover');
        }
      });
    });
  }
}

// Initialize cursor animation when DOM is loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    new CursorAnimation();
  });
} else {
  new CursorAnimation();
}
