import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.detector.gatekeeper import classify_job_relevance
from backend.app.detector.aggregator import analyse


def test_gatekeeper_job_postings():
    # 1. Legit Job Posting
    stripe_job = """
    We are seeking a Senior Backend Engineer to join our cloud platform team at Stripe.
    Responsibilities: Design and implement high-throughput REST APIs and Kafka microservices.
    Requirements: 4+ years experience with Go or Python, relational databases, and distributed systems.
    Benefits: Competitive compensation, 401(k) matching, comprehensive health insurance.
    To apply, submit your resume on our careers portal at https://stripe.com/jobs or contact recruiting@stripe.com.
    """
    res1 = classify_job_relevance(stripe_job)
    print(f"Stripe job posting: is_job={res1['is_job_posting']}, type={res1['content_type']}, conf={res1['confidence']}")
    assert res1["is_job_posting"] is True
    assert "job" in res1["content_type"]

    # 2. Student Internship Scam (User case)
    intern_scam = """
    We are happy to offer you an opportunity to work as a Marketing intern for pursuing students (part-time job) where you can earn more than your Pocket money. Immediate Hiring, just pay 5000 initially
    Your opportunity involves:
    * Work from home
    * Branding/Promotion
    * Good Stipend (2500-21000)
    * Marketing Intern certificate 
    * Free internship opportunity
    * Letter of recommendation 
    TO APPLY FILL: NAME, COLLEGE, BRANCH&YEAR, PH, EMAIL
    """
    res2 = classify_job_relevance(intern_scam)
    print(f"Intern scam: is_job={res2['is_job_posting']}, type={res2['content_type']}, conf={res2['confidence']}")
    assert res2["is_job_posting"] is True


def test_gatekeeper_non_job_content():
    # 1. Recipe
    recipe = """
    Delicious Homemade Chocolate Brownies Recipe
    Ingredients:
    - 200g dark chocolate, chopped
    - 150g unsalted butter
    - 200g brown sugar
    - 3 large eggs
    - 100g all-purpose flour
    - 30g cocoa powder
    
    Instructions:
    Preheat your oven to 180°C (350°F). Melt butter and chocolate together in a bowl over simmering water.
    Whisk eggs and sugar until pale and fluffy, then fold in the melted chocolate.
    Bake for 25-30 minutes until top is crackled.
    """
    res_recipe = classify_job_relevance(recipe)
    print(f"Recipe: is_job={res_recipe['is_job_posting']}, type={res_recipe['content_type']}")
    assert res_recipe["is_job_posting"] is False

    # 2. Candidate Resume / CV (Common mistake: candidates paste their CV instead of job ad)
    resume = """
    CURRICULUM VITAE
    Rahul Sharma
    Email: rahul.sharma@gmail.com | Phone: +91 9876543210
    
    CAREER OBJECTIVE:
    Motivated Computer Science graduate seeking an entry-level Software Developer position to utilize skills in Python, Java, and web development.
    
    EDUCATION:
    B.Tech in Computer Science and Engineering - 8.6 CGPA (2020-2024)
    Govt Engineering College
    
    ACADEMIC PROJECTS:
    - Smart Attendance System using Face Recognition (Python, OpenCV)
    - E-Commerce Web Application (React, Node.js, MongoDB)
    
    DECLARATION:
    I hereby declare that all the information provided above is true to the best of my knowledge.
    """
    res_cv = classify_job_relevance(resume)
    print(f"Candidate CV: is_job={res_cv['is_job_posting']}, type={res_cv['content_type']}")
    assert res_cv["is_job_posting"] is False
    assert "resume" in res_cv["content_type"]

    # 3. Casual chat
    chat = """
    Hey bro, are you coming to college tomorrow?
    The professor said the seminar starts at 9:30 AM sharp.
    Don't forget to bring the project report printout we finalized yesterday!
    Let's catch up at the cafeteria after lunch.
    """
    res_chat = classify_job_relevance(chat)
    print(f"Casual Chat: is_job={res_chat['is_job_posting']}, type={res_chat['content_type']}")
    assert res_chat["is_job_posting"] is False

    # 4. Grocery receipt / invoice
    receipt = """
    SUPERMARKET GROCERY STORE
    TAX INVOICE / CASH RECEIPT
    Date: 04/10/2026  Time: 14:22
    Cashier: Counter 04
    -------------------------------------------
    Item                    Qty    Price  Total
    Fresh Milk 1L            2     $3.50  $7.00
    Brown Bread              1     $2.20  $2.20
    Subtotal:                             $14.10
    Tax (5%):                              $0.70
    TOTAL AMOUNT DUE:                     $14.80
    Paid by Visa Card Ending in 4242
    Thank you for shopping with us!
    """
    res_receipt = classify_job_relevance(receipt)
    print(f"Receipt: is_job={res_receipt['is_job_posting']}, type={res_receipt['content_type']}")
    assert res_receipt["is_job_posting"] is False


def test_aggregator_with_gatekeeper():
    # Analyze a recipe through aggregator
    recipe = """
    Spaghetti Carbonara Recipe:
    Boil salted water and cook spaghetti for 9 minutes.
    In a bowl, mix egg yolks, grated pecorino cheese, and black pepper.
    Preheat oven or skillet. Fry guanciale in a pan until crispy.
    Toss hot pasta with egg mixture and crispy pork. Serve immediately with extra cheese.
    """
    result = analyse(recipe)
    print("\nAggregator on Recipe:")
    print("  is_job_posting      :", result["is_job_posting"])
    print("  risk_score          :", result["risk_score"])
    print("  risk_level          :", result["risk_level"])
    print("  verdict             :", result["verdict"])
    print("  gatekeeper_reasoning:", result["gatekeeper_reasoning"])

    assert result["is_job_posting"] is False
    assert result["risk_score"] is None
    assert result["risk_level"] == "Invalid Content"
    assert "rather than a job vacancy" in result["verdict"]


if __name__ == "__main__":
    test_gatekeeper_job_postings()
    test_gatekeeper_non_job_content()
    test_aggregator_with_gatekeeper()
    print("\nAll Gatekeeper tests passed successfully!")
