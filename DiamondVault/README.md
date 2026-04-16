# DiamondVault - Diamond Auction Platform

A sophisticated Django-based auction platform for buying and selling diamonds online with integrated payment processing.

## Features

- **Diamond Management**: Add, edit, and manage diamond inventory with detailed specifications
- **Live Auctions**: Real-time bidding system with countdown timers
- **User Authentication**: Secure user registration and login system
- **Payment Integration**: Razorpay payment gateway integration
- **Winner Dashboard**: Track auction wins and payment history
- **Advanced Filtering**: Search diamonds by carat weight and other specifications
- **Responsive Design**: Modern, mobile-friendly interface using Bootstrap

## Tech Stack

- **Backend**: Django 4.2.6
- **Database**: SQLite (development)
- **Frontend**: HTML5, CSS3, Bootstrap 5
- **JavaScript**: Vanilla JS for real-time features
- **Payment**: Razorpay API
- **Authentication**: Django's built-in auth system

## Installation

### Prerequisites

- Python 3.11+
- Django 4.2.6
- Razorpay account for payment processing

### Setup

1. Clone the repository:
```bash
git clone https://github.com/shanidhruv808-oss/my_project.git
cd my_project
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install django razorpay
```

4. Configure settings:
   - Add your Razorpay API keys to `DiamondVault/settings.py`
   - Update `ALLOWED_HOSTS` for your domain

5. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

## Configuration

### Razorpay Setup

1. Create a Razorpay account at [razorpay.com](https://razorpay.com)
2. Get your API keys from the Razorpay dashboard
3. Add the keys to your `settings.py`:
```python
RAZORPAY_KEY_ID = 'your_key_id'
RAZORPAY_KEY_SECRET = 'your_key_secret'
```

### Environment Variables

Create a `.env` file in the project root:
```
DEBUG=True
SECRET_KEY=your_secret_key
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_key_secret
```

## Usage

### Adding Diamonds

1. Access the Django admin panel at `/admin/`
2. Add diamond details including:
   - Name, carat, color, clarity, cut
   - Base price and images
   - Auction timing

### Auction Process

1. Users browse available diamonds
2. Place bids during active auction periods
3. Winner is automatically assigned when auction ends
4. Winner can complete payment using Razorpay
5. Order is created and tracked in winner dashboard

### Payment Flow

1. Winner clicks "Pay Now" button
2. Razorpay payment modal opens
3. Payment is processed securely
4. Order is created upon successful payment
5. Receipt is available in winner dashboard

## Project Structure

```
DiamondVault/
    auction/
        migrations/
        templates/
        __init__.py
        admin.py
        apps.py
        models.py
        tests.py
        urls.py
        views.py
    DiamondVault/
        __init__.py
        settings.py
        urls.py
        wsgi.py
    templates/
        base.html
        about.html
        diamond_detail.html
        diamonds.html
        index.html
        login.html
        payment_new.html
        etc.
    media/
    static/
    manage.py
```

## API Endpoints

- `/` - Home page with active auctions
- `/diamonds/` - Browse all diamonds
- `/diamond/<id>/` - Diamond detail and bidding
- `/payment/<auction_id>/` - Payment processing
- `/winner-dashboard/` - User's auction wins
- `/about/` - About page

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please open an issue on GitHub.

## Future Enhancements

- Email notifications for auction updates
- Advanced search and filtering options
- Mobile app development
- Multi-currency support
- Auction analytics dashboard
- Social media integration

---

**Developed by**: Shanidhruv808-oss  
**Version**: 1.0.0
