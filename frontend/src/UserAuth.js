import React, { useState, useEffect } from "react";
import axios from "axios";
import { 
  User, 
  Heart,
  History,
  Settings,
  LogOut,
  Eye,
  EyeOff,
  Star,
  MapPin,
  X
} from "lucide-react";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Alert, AlertDescription } from "./components/ui/alert";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const UserAuth = ({ onClose, onUserLogin, currentFavorites = [], onFavoritesUpdate }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('user_token'));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Auth states
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [authForm, setAuthForm] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: ''
  });

  // User data states - use favorites data passed from parent
  const [favorites, setFavorites] = useState([]);

  useEffect(() => {
    if (token) {
      fetchUserData();
    }
  }, [token]);

  // Update local favorites when parent favorites change
  useEffect(() => {
    if (currentFavorites.length > 0) {
      fetchFavoritesDetails();
    } else {
      setFavorites([]);
    }
  }, [currentFavorites, token]);

  const fetchFavoritesDetails = async () => {
    try {
      if (token && currentFavorites.length > 0) {
        const response = await axios.get(`${API}/users/favorites`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        console.log('UserAuth - Fetched favorites details:', response.data.favorites);
        setFavorites(response.data.favorites);
      }
    } catch (error) {
      console.error('Error fetching favorite details:', error);
    }
  };

  const fetchUserData = async () => {
    try {
      const response = await axios.get(`${API}/users/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
      onUserLogin(response.data); // Notify parent component
      fetchFavorites();
    } catch (error) {
      console.error('Error fetching user data:', error);
      if (error.response?.status === 401) {
        handleLogout();
      }
    }
  };

  const fetchFavorites = async () => {
    try {
      const response = await axios.get(`${API}/users/favorites`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFavorites(response.data.favorites);
    } catch (error) {
      console.error('Error fetching favorites:', error);
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const endpoint = isLogin ? '/users/login' : '/users/register';
      const response = await axios.post(`${API}${endpoint}`, authForm);
      
      const { access_token, user: userData } = response.data;
      localStorage.setItem('user_token', access_token);
      setToken(access_token);
      setUser(userData);
      setSuccess(response.data.message);
      onUserLogin(userData);
      
      // Reset form
      setAuthForm({
        email: '',
        password: '',
        first_name: '',
        last_name: ''
      });
      
    } catch (error) {
      setError(error.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('user_token');
    setToken(null);
    setUser(null);
    setFavorites([]);
    onUserLogin(null);
  };

  const removeFavorite = async (restaurantId) => {
    try {
      await axios.delete(`${API}/users/favorites/${restaurantId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setFavorites(favorites.filter(fav => fav.id !== restaurantId));
      setSuccess('Restaurant removed from favorites');
    } catch (error) {
      setError('Failed to remove favorite');
    }
  };

  // If not logged in, show auth form
  if (!user) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <Card className="w-full max-w-md relative">
          <button
            onClick={onClose}
            className="absolute right-4 top-4 text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
          
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold text-gray-900">
              {isLogin ? 'Welcome Back!' : 'Join On-the-Cheap'}
            </CardTitle>
            <CardDescription>
              {isLogin ? 'Sign in to save favorites and get personalized deals' : 'Create an account to save your favorite restaurants'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAuth} className="space-y-4">
              {!isLogin && (
                <div className="grid grid-cols-2 gap-2">
                  <Input
                    placeholder="First Name"
                    value={authForm.first_name}
                    onChange={(e) => setAuthForm({...authForm, first_name: e.target.value})}
                    required
                  />
                  <Input
                    placeholder="Last Name"
                    value={authForm.last_name}
                    onChange={(e) => setAuthForm({...authForm, last_name: e.target.value})}
                    required
                  />
                </div>
              )}
              
              <div>
                <Input
                  type="email"
                  placeholder="Email Address"
                  value={authForm.email}
                  onChange={(e) => setAuthForm({...authForm, email: e.target.value})}
                  required
                />
              </div>
              
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  placeholder="Password"
                  value={authForm.password}
                  onChange={(e) => setAuthForm({...authForm, password: e.target.value})}
                  required
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 transform -translate-y-1/2"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>

              {error && (
                <Alert className="border-red-200 bg-red-50">
                  <AlertDescription className="text-red-800">{error}</AlertDescription>
                </Alert>
              )}

              {success && (
                <Alert className="border-green-200 bg-green-50">
                  <AlertDescription className="text-green-800">{success}</AlertDescription>
                </Alert>
              )}

              <Button 
                type="submit" 
                className="w-full bg-orange-600 hover:bg-orange-700"
                disabled={loading}
              >
                {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Create Account')}
              </Button>
            </form>

            <div className="mt-4 text-center">
              <button
                type="button"
                onClick={() => {
                  setIsLogin(!isLogin);
                  setError('');
                  setSuccess('');
                }}
                className="text-orange-600 hover:underline"
              >
                {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // User dashboard
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-4xl max-h-[90vh] overflow-y-auto relative">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-gray-400 hover:text-gray-600 z-10"
        >
          <X className="w-5 h-5" />
        </button>
        
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle className="text-2xl font-bold text-gray-900">
                Welcome, {user.first_name}!
              </CardTitle>
              <CardDescription>
                Manage your favorites and preferences
              </CardDescription>
            </div>
            <Button variant="outline" onClick={handleLogout}>
              <LogOut className="w-4 h-4 mr-2" />
              Sign Out
            </Button>
          </div>
        </CardHeader>

        <CardContent>
          {error && (
            <Alert className="mb-4 border-red-200 bg-red-50">
              <AlertDescription className="text-red-800">{error}</AlertDescription>
            </Alert>
          )}

          {success && (
            <Alert className="mb-4 border-green-200 bg-green-50">
              <AlertDescription className="text-green-800">{success}</AlertDescription>
            </Alert>
          )}

          <Tabs defaultValue="favorites" className="space-y-6">
            <TabsList>
              <TabsTrigger value="favorites">My Favorites</TabsTrigger>
              <TabsTrigger value="profile">Profile</TabsTrigger>
            </TabsList>

            {/* Favorites Tab */}
            <TabsContent value="favorites">
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">Favorite Restaurants ({favorites.length})</h3>
                
                {favorites.length === 0 ? (
                  <div className="text-center py-8">
                    <Heart className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                    <h4 className="text-lg font-medium text-gray-900 mb-2">No favorites yet</h4>
                    <p className="text-gray-600 mb-4">
                      Start exploring restaurants and save your favorites!
                    </p>
                    <Button onClick={onClose} className="bg-orange-600 hover:bg-orange-700">
                      Discover Restaurants
                    </Button>
                  </div>
                ) : (
                  <div className="grid gap-4 md:grid-cols-2">
                    {favorites.map((restaurant) => (
                      <Card key={restaurant.id} className="hover:shadow-md transition-shadow">
                        <CardContent className="p-4">
                          <div className="flex justify-between items-start mb-2">
                            <h4 className="font-semibold text-gray-900">{restaurant.name}</h4>
                            <button
                              onClick={() => removeFavorite(restaurant.id)}
                              className="text-red-500 hover:text-red-700"
                            >
                              <Heart className="w-4 h-4 fill-current" />
                            </button>
                          </div>
                          
                          <p className="text-sm text-gray-600 mb-2 flex items-center">
                            <MapPin className="w-3 h-3 mr-1" />
                            {restaurant.address}
                          </p>
                          
                          {restaurant.rating && (
                            <p className="text-sm text-gray-600 mb-2 flex items-center">
                              <Star className="w-3 h-3 mr-1 text-yellow-400 fill-current" />
                              {restaurant.rating}
                            </p>
                          )}
                          
                          <div className="flex flex-wrap gap-1 mb-2">
                            {restaurant.cuisine_type?.slice(0, 2).map((cuisine) => (
                              <Badge key={cuisine} variant="secondary" className="text-xs">
                                {cuisine}
                              </Badge>
                            ))}
                          </div>
                          
                          <p className="text-xs text-gray-500">
                            {restaurant.specials_count} active specials
                          </p>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            </TabsContent>

            {/* Profile Tab */}
            <TabsContent value="profile">
              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold mb-4">Profile Information</h3>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        First Name
                      </label>
                      <Input value={user.first_name} disabled />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Last Name
                      </label>
                      <Input value={user.last_name} disabled />
                    </div>
                    <div className="md:col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Email
                      </label>
                      <Input value={user.email} disabled />
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold mb-4">Account Statistics</h3>
                  <div className="grid gap-4 md:grid-cols-3">
                    <Card>
                      <CardContent className="p-4 text-center">
                        <Heart className="w-8 h-8 mx-auto text-red-500 mb-2" />
                        <h4 className="font-semibold text-2xl">{favorites.length}</h4>
                        <p className="text-sm text-gray-600">Favorite Restaurants</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4 text-center">
                        <User className="w-8 h-8 mx-auto text-orange-500 mb-2" />
                        <h4 className="font-semibold text-2xl">Member</h4>
                        <p className="text-sm text-gray-600">Account Status</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4 text-center">
                        <Settings className="w-8 h-8 mx-auto text-gray-500 mb-2" />
                        <h4 className="font-semibold text-2xl">Active</h4>
                        <p className="text-sm text-gray-600">Profile Status</p>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

export default UserAuth;