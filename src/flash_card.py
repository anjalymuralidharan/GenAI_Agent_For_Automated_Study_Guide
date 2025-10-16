import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import os
import random
import io

class FlashcardGenerator:
    def __init__(self, question_templates_dir="templates/questions", 
                 answer_templates_dir="templates/answers"):
        """
        Initialize with directories containing your Canva template images
        Templates should be PNG/JPG images
        """
        # Get the absolute path of the current file's directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Go up one level to the project root if we're in the src directory
        if os.path.basename(current_dir) == "src":
            project_root = os.path.dirname(current_dir)
        else:
            project_root = current_dir
            
        # Construct absolute paths for template directories
        self.question_templates_dir = os.path.join(project_root, "src", "templates", "questions")
        self.answer_templates_dir = os.path.join(project_root, "src", "templates", "answers")
        
        # Create directories if they don't exist
        os.makedirs(self.question_templates_dir, exist_ok=True)
        os.makedirs(self.answer_templates_dir, exist_ok=True)
        
        # Load templates using absolute paths
        self.question_templates = self._load_templates(self.question_templates_dir)
        self.answer_templates = self._load_templates(self.answer_templates_dir)
        
        # Log template loading results for debugging
        print(f"Loading templates from: {self.question_templates_dir}")
        print(f"Found {len(self.question_templates)} question templates")
        print(f"Found {len(self.answer_templates)} answer templates")
        
        if not self.question_templates or not self.answer_templates:
            print("Warning: No templates found in directories:")
        
        self.margin = 50
        
    def _load_templates(self, directory):
        """Load all image templates from directory"""
        templates = []
        
        # Check if directory exists
        if not os.path.exists(directory):
            print(f"Warning: Template directory not found: {directory}")
            return templates
            
        try:
            # List all files in directory
            files = os.listdir(directory)
            print(f"Found files in {directory}: {files}")  # Debug log
            
            # Filter and add valid image files
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    template_path = os.path.join(directory, file)
                    # Verify the image can be opened
                    try:
                        with Image.open(template_path) as img:
                            # Convert relative path to absolute if needed
                            abs_path = os.path.abspath(template_path)
                            templates.append(abs_path)
                            print(f"Successfully loaded template: {abs_path}")
                    except Exception as e:
                        print(f"Error loading template {template_path}: {str(e)}")
            
            print(f"Loaded {len(templates)} templates from {directory}")
            
        except Exception as e:
            print(f"Error accessing template directory {directory}: {str(e)}")
        
        return templates
    
    def load_font(self, size=28):
        """Load font with fallback"""
        try:
            return ImageFont.truetype("arial.ttf", size=size)
        except:
            try:
                return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=size)
            except:
                return ImageFont.load_default()
    
    def get_text_bbox(self, text, font):
        """Get text dimensions"""
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    def wrap_text(self, text, font, max_width):
        """Wrap text to fit width"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            width, _ = self.get_text_bbox(test_line, font)
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def scale_font_size_to_fit(self, text, font, max_width, max_height):
        """
        Scale down the font size dynamically until the text fits within max_width and max_height.
        """
        # Start with the given font size
        font_size = font.size
        # Wrap text to see if it fits
        lines = self.wrap_text(text, font, max_width)
        
        # Calculate total height of the wrapped text
        total_height = sum([self.get_text_bbox(line, font)[1] for line in lines]) + (len(lines) - 1) * 15

        # Decrease font size until the total height is less than max_height
        while total_height > max_height and font_size > 10:  # Avoid going below size 10
            font_size -= 2  # Decrease font size by 2
            font = self.load_font(size=font_size)  # Reload font with the new size
            lines = self.wrap_text(text, font, max_width)  # Rewrap text with new font size
            total_height = sum([self.get_text_bbox(line, font)[1] for line in lines]) + (len(lines) - 1) * 15

        return font, lines  # Return new font and wrapped lines

    
    def add_text_to_template(self, template_path, text, text_color="#000000"):
        """Overlay text on template image with dynamic font scaling"""
        # Load template
        card = Image.open(template_path).convert('RGB')
        draw = ImageDraw.Draw(card)

        width, height = card.size
        max_text_width = width - (2 * self.margin)
        max_text_height = height - (2 * self.margin)  # Ensure text fits in the height as well

        # Load initial font (starting font size can be adjusted)
        font = self.load_font(size=32)

        # Scale the font size dynamically to fit
        font, lines = self.scale_font_size_to_fit(text, font, max_text_width, max_text_height)

        # Calculate total height of wrapped text
        line_heights = [self.get_text_bbox(line, font)[1] for line in lines]
        total_height = sum(line_heights) + (len(lines) - 1) * 15

        # Center vertically
        start_y = (height - total_height) // 2

        # Draw each line centered
        current_y = start_y
        for line in lines:
            text_width, text_height = self.get_text_bbox(line, font)
            text_x = (width - text_width) // 2

            # Add subtle shadow for better readability
            draw.text((text_x + 2, current_y + 2), line, font=font, fill="#00000040")
            # Add the main text
            draw.text((text_x, current_y), line, font=font, fill=text_color)

            current_y += text_height + 15

        return card

    
    def create_flashcard_pair(self, question, answer, question_template=None):
        # Use the provided question_template instead of random choice
        answer_template = None
        if question_template and self.answer_templates:
            # Extract filename of question template (e.g., '3.jpg')
            question_filename = os.path.basename(question_template)

            # Find answer template with the same filename
            for ans_tpl in self.answer_templates:
                if os.path.basename(ans_tpl) == question_filename:
                    answer_template = ans_tpl
                    break

            # If not found, fallback to random answer template
            if not answer_template:
                answer_template = random.choice(self.answer_templates)
        else:
            # No templates found, keep None to fallback later
            answer_template = None

        # If no templates, create simple colored cards
        if not question_template:
            front = self._create_simple_card(question, "QUESTION", "#4A90E2", "#FFFFFF")
        else:
            # Use white text for template-based cards for better visibility
            front = self.add_text_to_template(question_template, question, "#FFFFFF")

        if not answer_template:
            back = self._create_simple_card(answer, "ANSWER", "#27AE60", "#FFFFFF")
        else:
            # Use white text for template-based cards for better visibility
            back = self.add_text_to_template(answer_template, answer, "#FFFFFF")

        return front, back

    def _create_simple_card(self, text, label, bg_color, text_color):
        """Fallback: Create simple colored card if no templates"""
        card = Image.new('RGB', (800, 500), color=bg_color)
        draw = ImageDraw.Draw(card)
        
        font = self.load_font(size=36)
        label_font = self.load_font(size=20)
        
        # Label
        draw.text((20, 20), label, font=label_font, fill=text_color)
        
        # Text
        lines = self.wrap_text(text, font, 700)
        line_heights = [self.get_text_bbox(line, font)[1] for line in lines]
        total_height = sum(line_heights) + (len(lines) - 1) * 15
        start_y = (500 - total_height) // 2
        
        current_y = start_y
        for line in lines:
            text_width, text_height = self.get_text_bbox(line, font)
            text_x = (800 - text_width) // 2
            draw.text((text_x, current_y), line, font=font, fill=text_color)
            current_y += text_height + 15
        
        return card

def main():
    st.set_page_config(page_title="Flashcards!!", page_icon="🎴", layout="centered")
    
    # Minimal styling
    st.markdown("""
        <style>
        .main {background-color: #1a1a1a;}
        .stButton>button {
            width: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-size: 16px;
            padding: 12px;
            border-radius: 12px;
            border: none;
            font-weight: 600;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize QA dict if not already
    if 'qa_dict' not in st.session_state:
        st.session_state.qa_dict = {
            "What is machine learning?": 
                "Machine learning is a subset of AI that enables systems to learn and improve from experience without being explicitly programmed.",
            
            "What is a neural network?": 
                "A neural network is a computing system inspired by biological neural networks that learns to perform tasks by considering examples.",
            
            "What is deep learning?": 
                "Deep learning is a subset of machine learning that uses neural networks with multiple layers to progressively extract higher-level features.",
        }
    
    if 'idx' not in st.session_state:
        st.session_state.idx = 0
    
    if 'show_front' not in st.session_state:
        st.session_state.show_front = True

    # Initialize the FlashcardGenerator and question-template map once
    if 'question_templates_map' not in st.session_state:
        try:
            generator = FlashcardGenerator()
            
            if not generator.question_templates:
                st.warning("⚠️ No template images found. Please ensure template folders exist and contain images.")
            else:
                st.success(f"✅ Found {len(generator.question_templates)} question templates and {len(generator.answer_templates)} answer templates.")
            
            st.session_state.question_templates_map = {}
            
            for q in st.session_state.qa_dict.keys():
                if generator.question_templates:
                    chosen_template = random.choice(generator.question_templates)
                else:
                    chosen_template = None
                st.session_state.question_templates_map[q] = chosen_template
            
            st.session_state.generator = generator
            
        except Exception as e:
            st.error(f"Error initializing flashcard generator: {str(e)}")
            generator = FlashcardGenerator()  # Fallback to default paths
            st.session_state.generator = generator
            st.session_state.question_templates_map = {}

    questions = list(st.session_state.qa_dict.keys())
    if not questions:
        st.warning("No cards available")
        return
    
    current_q = questions[st.session_state.idx]
    current_a = st.session_state.qa_dict[current_q]

    st.markdown(
        f"<p style='text-align: center; color: #888;'>{st.session_state.idx + 1} / {len(questions)}</p>",
        unsafe_allow_html=True
    )

    # Get the question template for current question
    question_template = st.session_state.question_templates_map.get(current_q, None)

    # Generate flashcard pair using the stored template
    front, back = st.session_state.generator.create_flashcard_pair(current_q, current_a, question_template=question_template)

    def pil_to_bytes(pil_img):
        buf = io.BytesIO()
        pil_img.save(buf, format='JPEG')
        buf.seek(0)
        return buf

    if st.session_state.show_front:
        st.image(pil_to_bytes(front), use_container_width=True)
    else:
        st.image(pil_to_bytes(back), use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🔄 FLIP"):
        st.session_state.show_front = not st.session_state.show_front
        st.rerun()

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("⬅️ PREV"):
            st.session_state.idx = (st.session_state.idx - 1) % len(questions)
            st.session_state.show_front = True
            st.rerun()

    with col2:
        if st.button("🔀 RANDOM"):
            st.session_state.idx = random.randint(0, len(questions) - 1)
            st.session_state.show_front = True
            st.rerun()

    with col3:
        if st.button("NEXT ➡️"):
            st.session_state.idx = (st.session_state.idx + 1) % len(questions)
            st.session_state.show_front = True
            st.rerun()

if __name__ == "__main__":
    main()
