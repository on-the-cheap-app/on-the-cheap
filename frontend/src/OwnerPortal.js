import React, { useState, useEffect } from "react";
import axios from "axios";
import { 
  User, 
  Building2, 
  Plus, 
  Edit, 
  Trash2, 
  Clock, 
  DollarSign, 
  Calendar,
  Search,
  CheckCircle,
  AlertCircle,
  Settings,
  LogOut,
  Eye,
  EyeOff
} from "lucide-react";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Textarea } from "./components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Alert, AlertDescription } from "./components/ui/alert";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const OwnerPortal = () => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('owner_token'));
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
    last_name: '',
    business_name: '',
    phone: ''
  });

  // Restaurant management states
  const [myRestaurants, setMyRestaurants] = useState([]);
  const [pendingClaims, setPendingClaims] = useState([]);
  const [searchResults, setSearchResults] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRestaurant, setSelectedRestaurant] = useState(null);
  const [restaurantSpecials, setRestaurantSpecials] = useState([]);
  
  // Special form states
  const [specialForm, setSpecialForm] = useState({
    title: '',
    description: '',
    special_type: '',
    price: '',
    original_price: '',
    days_available: [],
    time_start: '',
    time_end: ''
  });
  const [editingSpecial, setEditingSpecial] = useState(null);

  const specialTypes = [
    { value: "happy_hour", label: "Happy Hour" },
    { value: "lunch_special", label: "Lunch Special" },
    { value: "dinner_special", label: "Dinner Special" },
    { value: "blue_plate", label: "Blue Plate Special" },
    { value: "daily_special", label: "Daily Special" },
    { value: "weekend_special", label: "Weekend Special" }
  ];

  const daysOfWeek = [
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
  ];

  useEffect(() => {
    if (token) {
      fetchUserData();
    }
  }, [token]);

  const fetchUserData = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
      fetchMyRestaurants();
    } catch (error) {
      console.error('Error fetching user data:', error);
      if (error.response?.status === 401) {
        handleLogout();
      }
    }
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const response = await axios.post(`${API}${endpoint}`, authForm);
      
      const { access_token, user } = response.data;
      localStorage.setItem('owner_token', access_token);
      setToken(access_token);
      setUser(user);
      setSuccess(response.data.message);
      
      // Reset form
      setAuthForm({
        email: '',
        password: '',
        first_name: '',
        last_name: '',
        business_name: '',
        phone: ''
      });
      
    } catch (error) {
      setError(error.response?.data?.detail || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('owner_token');
    setToken(null);
    setUser(null);
    setMyRestaurants([]);
    setPendingClaims([]);
  };

  const fetchMyRestaurants = async () => {
    try {
      const response = await axios.get(`${API}/owner/my-restaurants`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMyRestaurants(response.data.restaurants);
      setPendingClaims(response.data.pending_claims);
    } catch (error) {
      console.error('Error fetching restaurants:', error);
    }
  };

  const searchRestaurantsToShow = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${API}/owner/search-restaurants`, {
        params: { query: searchQuery },
        headers: { Authorization: `Bearer ${token}` }
      });
      setSearchResults(response.data.restaurants);
    } catch (error) {
      setError('Search failed');
    } finally {
      setLoading(false);
    }
  };

  const claimRestaurant = async (restaurant) => {
    try {
      await axios.post(`${API}/owner/claim-restaurant`, {
        google_place_id: restaurant.id.replace('google_', ''),
        business_name: restaurant.name,
        verification_notes: `Claiming ${restaurant.name} - ${restaurant.address}`
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setSuccess('Restaurant claim submitted for approval');
      fetchMyRestaurants();
      
      // Update search results
      setSearchResults(prev => prev.map(r => 
        r.id === restaurant.id ? { ...r, is_claimed: true, claim_status: 'pending' } : r
      ));
    } catch (error) {
      setError(error.response?.data?.detail || 'Claim failed');
    }
  };

  const fetchRestaurantSpecials = async (restaurantId) => {
    try {
      const response = await axios.get(`${API}/owner/restaurants/${restaurantId}/specials`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRestaurantSpecials(response.data.specials);
    } catch (error) {
      console.error('Error fetching specials:', error);
    }
  };

  const handleSpecialSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const specialData = {
        ...specialForm,
        price: specialForm.price ? parseFloat(specialForm.price) : null,
        original_price: specialForm.original_price ? parseFloat(specialForm.original_price) : null
      };

      if (editingSpecial) {
        await axios.put(`${API}/owner/restaurants/${selectedRestaurant.id}/specials/${editingSpecial.id}`, 
          specialData, {
            headers: { Authorization: `Bearer ${token}` }
          });
        setSuccess('Special updated successfully');
      } else {
        await axios.post(`${API}/owner/restaurants/${selectedRestaurant.id}/specials`, 
          specialData, {
            headers: { Authorization: `Bearer ${token}` }
          });
        setSuccess('Special created successfully');
      }

      // Reset form and refresh specials
      setSpecialForm({
        title: '', description: '', special_type: '', price: '', original_price: '',
        days_available: [], time_start: '', time_end: ''
      });
      setEditingSpecial(null);
      fetchRestaurantSpecials(selectedRestaurant.id);
      
    } catch (error) {
      setError(error.response?.data?.detail || 'Operation failed');
    } finally {
      setLoading(false);
    }
  };

  const handleEditSpecial = (special) => {
    setSpecialForm({
      title: special.title,
      description: special.description,
      special_type: special.special_type,
      price: special.price?.toString() || '',
      original_price: special.original_price?.toString() || '',
      days_available: special.days_available,
      time_start: special.time_start,
      time_end: special.time_end
    });
    setEditingSpecial(special);
  };

  const handleDeleteSpecial = async (specialId) => {
    if (!confirm('Are you sure you want to delete this special?')) return;

    try {
      await axios.delete(`${API}/owner/restaurants/${selectedRestaurant.id}/specials/${specialId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSuccess('Special deleted successfully');
      fetchRestaurantSpecials(selectedRestaurant.id);
    } catch (error) {
      setError('Delete failed');
    }
  };

  const formatTime = (timeStr) => {
    if (!timeStr) return '';
    const [hours, minutes] = timeStr.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
  };

  // If not logged in, show auth form
  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-amber-50 to-orange-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold text-gray-900">
              {isLogin ? 'Restaurant Owner Login' : 'Register Your Restaurant'}
            </CardTitle>
            <CardDescription>
              {isLogin ? 'Access your restaurant dashboard' : 'Join On-the-Cheap today'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleAuth} className="space-y-4">
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

              {!isLogin && (
                <>
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
                  
                  <Input
                    placeholder="Business Name"
                    value={authForm.business_name}
                    onChange={(e) => setAuthForm({...authForm, business_name: e.target.value})}
                    required
                  />
                  
                  <Input
                    placeholder="Phone Number"
                    value={authForm.phone}
                    onChange={(e) => setAuthForm({...authForm, phone: e.target.value})}
                    required
                  />
                </>
              )}

              {error && (
                <Alert className="border-red-200 bg-red-50">
                  <AlertCircle className="w-4 h-4 text-red-600" />
                  <AlertDescription className="text-red-800">{error}</AlertDescription>
                </Alert>
              )}

              {success && (
                <Alert className="border-green-200 bg-green-50">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <AlertDescription className="text-green-800">{success}</AlertDescription>
                </Alert>
              )}

              <Button 
                type="submit" 
                className="w-full bg-orange-600 hover:bg-orange-700"
                disabled={loading}
              >
                {loading ? 'Processing...' : (isLogin ? 'Login' : 'Register')}
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
                {isLogin ? "Don't have an account? Register" : "Already have an account? Login"}
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Main dashboard
  return (
    <div className="min-h-screen bg-gradient-to-b from-amber-50 to-orange-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Restaurant Owner Portal</h1>
              <p className="text-gray-600">Welcome back, {user.first_name}!</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="text-right">
                <p className="font-medium text-gray-900">{user.business_name}</p>
                <p className="text-sm text-gray-600">{user.email}</p>
              </div>
              <Button variant="outline" onClick={handleLogout}>
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6">
        {error && (
          <Alert className="mb-4 border-red-200 bg-red-50">
            <AlertCircle className="w-4 h-4 text-red-600" />
            <AlertDescription className="text-red-800">{error}</AlertDescription>
          </Alert>
        )}

        {success && (
          <Alert className="mb-4 border-green-200 bg-green-50">
            <CheckCircle className="w-4 h-4 text-green-600" />
            <AlertDescription className="text-green-800">{success}</AlertDescription>
          </Alert>
        )}

        <Tabs defaultValue="restaurants" className="space-y-6">
          <TabsList>
            <TabsTrigger value="restaurants">My Restaurants</TabsTrigger>
            <TabsTrigger value="claim">Claim Restaurant</TabsTrigger>
            <TabsTrigger value="specials">Manage Specials</TabsTrigger>
          </TabsList>

          {/* My Restaurants Tab */}
          <TabsContent value="restaurants">
            <div className="grid gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>My Restaurants ({myRestaurants.length})</CardTitle>
                  <CardDescription>
                    Restaurants you own and manage
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {myRestaurants.length === 0 ? (
                    <div className="text-center py-8">
                      <Building2 className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">No restaurants yet</h3>
                      <p className="text-gray-600 mb-4">Claim your first restaurant to get started</p>
                      <Button 
                        onClick={() => document.querySelector('[value="claim"]').click()}
                        className="bg-orange-600 hover:bg-orange-700"
                      >
                        Claim Restaurant
                      </Button>
                    </div>
                  ) : (
                    <div className="grid gap-4 md:grid-cols-2">
                      {myRestaurants.map((restaurant) => (
                        <Card key={restaurant.id} className="hover:shadow-md transition-shadow">
                          <CardContent className="p-4">
                            <div className="flex justify-between items-start mb-2">
                              <h3 className="font-semibold text-gray-900">{restaurant.name}</h3>
                              <Badge variant="secondary" className="bg-green-100 text-green-800">
                                Verified
                              </Badge>
                            </div>
                            <p className="text-sm text-gray-600 mb-3">{restaurant.address}</p>
                            <div className="flex justify-between items-center">
                              <span className="text-sm text-gray-500">
                                {restaurant.specials?.length || 0} specials
                              </span>
                              <Button
                                size="sm"
                                onClick={() => {
                                  setSelectedRestaurant(restaurant);
                                  fetchRestaurantSpecials(restaurant.id);
                                  document.querySelector('[value="specials"]').click();
                                }}
                                className="bg-orange-600 hover:bg-orange-700"
                              >
                                Manage Specials
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Pending Claims */}
              {pendingClaims.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Pending Claims ({pendingClaims.length})</CardTitle>
                    <CardDescription>
                      Restaurant claims awaiting approval
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {pendingClaims.map((claim) => (
                        <div key={claim.id} className="flex justify-between items-center p-3 bg-yellow-50 rounded-lg">
                          <div>
                            <h4 className="font-medium text-gray-900">{claim.business_name}</h4>
                            <p className="text-sm text-gray-600">
                              Submitted {new Date(claim.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <Badge className="bg-yellow-100 text-yellow-800">Pending Review</Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          {/* Claim Restaurant Tab */}
          <TabsContent value="claim">
            <Card>
              <CardHeader>
                <CardTitle>Claim Your Restaurant</CardTitle>
                <CardDescription>
                  Search for your restaurant and submit a claim to manage it
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="Search for your restaurant by name..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && searchRestaurantsToShow()}
                  />
                  <Button onClick={searchRestaurantsToShow} disabled={loading}>
                    <Search className="w-4 h-4 mr-2" />
                    Search
                  </Button>
                </div>

                {searchResults.length > 0 && (
                  <div className="space-y-3">
                    <h3 className="font-medium text-gray-900">Search Results</h3>
                    {searchResults.map((restaurant) => (
                      <div key={restaurant.id} className="flex justify-between items-center p-4 border rounded-lg">
                        <div>
                          <h4 className="font-medium text-gray-900">{restaurant.name}</h4>
                          <p className="text-sm text-gray-600">{restaurant.address}</p>
                          {restaurant.rating && (
                            <p className="text-sm text-gray-500">Rating: {restaurant.rating} ⭐</p>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          {restaurant.is_claimed ? (
                            <Badge className="bg-gray-100 text-gray-800">
                              {restaurant.claim_status === 'pending' ? 'Pending' : 'Already Claimed'}
                            </Badge>
                          ) : (
                            <Button
                              onClick={() => claimRestaurant(restaurant)}
                              className="bg-orange-600 hover:bg-orange-700"
                            >
                              Claim Restaurant
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Manage Specials Tab */}
          <TabsContent value="specials">
            {!selectedRestaurant ? (
              <Card>
                <CardContent className="text-center py-8">
                  <Settings className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Restaurant</h3>
                  <p className="text-gray-600">Choose a restaurant from "My Restaurants" to manage its specials</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-6">
                <Card>
                  <CardHeader>
                    <div className="flex justify-between items-center">
                      <div>
                        <CardTitle>Manage Specials - {selectedRestaurant.name}</CardTitle>
                        <CardDescription>Add, edit, and remove restaurant specials</CardDescription>
                      </div>
                      <Button
                        variant="outline"
                        onClick={() => setSelectedRestaurant(null)}
                      >
                        Back to Restaurants
                      </Button>
                    </div>
                  </CardHeader>
                </Card>

                {/* Add/Edit Special Form */}
                <Card>
                  <CardHeader>
                    <CardTitle>
                      {editingSpecial ? 'Edit Special' : 'Add New Special'}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={handleSpecialSubmit} className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <Input
                          placeholder="Special Title"
                          value={specialForm.title}
                          onChange={(e) => setSpecialForm({...specialForm, title: e.target.value})}
                          required
                        />
                        
                        <Select 
                          value={specialForm.special_type} 
                          onValueChange={(value) => setSpecialForm({...specialForm, special_type: value})}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select Special Type" />
                          </SelectTrigger>
                          <SelectContent>
                            {specialTypes.map((type) => (
                              <SelectItem key={type.value} value={type.value}>
                                {type.label}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      <Textarea
                        placeholder="Description of the special..."
                        value={specialForm.description}
                        onChange={(e) => setSpecialForm({...specialForm, description: e.target.value})}
                        required
                      />

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <Input
                          type="number"
                          step="0.01"
                          placeholder="Special Price ($)"
                          value={specialForm.price}
                          onChange={(e) => setSpecialForm({...specialForm, price: e.target.value})}
                        />
                        
                        <Input
                          type="number"
                          step="0.01"
                          placeholder="Original Price ($)"
                          value={specialForm.original_price}
                          onChange={(e) => setSpecialForm({...specialForm, original_price: e.target.value})}
                        />
                        
                        <Input
                          type="time"
                          placeholder="Start Time"
                          value={specialForm.time_start}
                          onChange={(e) => setSpecialForm({...specialForm, time_start: e.target.value})}
                          required
                        />
                        
                        <Input
                          type="time"
                          placeholder="End Time"
                          value={specialForm.time_end}
                          onChange={(e) => setSpecialForm({...specialForm, time_end: e.target.value})}
                          required
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Available Days
                        </label>
                        <div className="flex flex-wrap gap-2">
                          {daysOfWeek.map((day) => (
                            <label key={day} className="flex items-center">
                              <input
                                type="checkbox"
                                checked={specialForm.days_available.includes(day)}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    setSpecialForm({
                                      ...specialForm,
                                      days_available: [...specialForm.days_available, day]
                                    });
                                  } else {
                                    setSpecialForm({
                                      ...specialForm,
                                      days_available: specialForm.days_available.filter(d => d !== day)
                                    });
                                  }
                                }}
                                className="mr-2"
                              />
                              <span className="text-sm capitalize">{day}</span>
                            </label>
                          ))}
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <Button
                          type="submit"
                          disabled={loading}
                          className="bg-orange-600 hover:bg-orange-700"
                        >
                          {loading ? 'Saving...' : (editingSpecial ? 'Update Special' : 'Add Special')}
                        </Button>
                        
                        {editingSpecial && (
                          <Button
                            type="button"
                            variant="outline"
                            onClick={() => {
                              setEditingSpecial(null);
                              setSpecialForm({
                                title: '', description: '', special_type: '', price: '', 
                                original_price: '', days_available: [], time_start: '', time_end: ''
                              });
                            }}
                          >
                            Cancel
                          </Button>
                        )}
                      </div>
                    </form>
                  </CardContent>
                </Card>

                {/* Current Specials */}
                <Card>
                  <CardHeader>
                    <CardTitle>Current Specials ({restaurantSpecials.length})</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {restaurantSpecials.length === 0 ? (
                      <div className="text-center py-8">
                        <Calendar className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                        <p className="text-gray-600">No specials yet. Add your first special above!</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {restaurantSpecials.map((special) => (
                          <div key={special.id} className="border rounded-lg p-4">
                            <div className="flex justify-between items-start mb-2">
                              <div>
                                <h4 className="font-medium text-gray-900">{special.title}</h4>
                                <p className="text-sm text-gray-600 mb-2">{special.description}</p>
                                
                                <div className="flex items-center gap-4 text-sm text-gray-500">
                                  {special.price && (
                                    <span className="flex items-center">
                                      <DollarSign className="w-3 h-3 mr-1" />
                                      ${special.price}
                                      {special.original_price && (
                                        <span className="ml-1 line-through">${special.original_price}</span>
                                      )}
                                    </span>
                                  )}
                                  
                                  <span className="flex items-center">
                                    <Clock className="w-3 h-3 mr-1" />
                                    {formatTime(special.time_start)} - {formatTime(special.time_end)}
                                  </span>
                                </div>
                                
                                <div className="mt-2">
                                  <span className="text-xs text-gray-500">
                                    {special.days_available.map(day => 
                                      day.charAt(0).toUpperCase() + day.slice(1)
                                    ).join(', ')}
                                  </span>
                                </div>
                              </div>
                              
                              <div className="flex items-center gap-2">
                                <Badge className={special.is_active ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-800"}>
                                  {special.is_active ? 'Active' : 'Inactive'}
                                </Badge>
                                
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleEditSpecial(special)}
                                >
                                  <Edit className="w-3 h-3" />
                                </Button>
                                
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleDeleteSpecial(special.id)}
                                  className="text-red-600 hover:text-red-700"
                                >
                                  <Trash2 className="w-3 h-3" />
                                </Button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default OwnerPortal;