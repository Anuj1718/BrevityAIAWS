import React, { createContext, useContext, useEffect, useState } from 'react';
import { auth } from '../../firebase/firebase';
import { onAuthStateChanged } from 'firebase/auth';
import { getUserProfile } from '../../firebase/Auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [useLoggedIn, setUseLoggedIn] = useState(false);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, initializeUser);
    return unsubscribe;
  },[])

  async function initializeUser(user) {
    if(user){
      setCurrentUser({...user});
      setUseLoggedIn(true);
      
      // Fetch user profile from Firestore
      try {
        const profile = await getUserProfile(user.uid);
        setUserProfile(profile);
      } catch (error) {
        console.error('Error fetching user profile:', error);
        setUserProfile(null);
      }
    }else{
      setCurrentUser(null);
      setUserProfile(null);
      setUseLoggedIn(false);
    }
    setLoading(false);
  }

  const value = {
    currentUser,
    userProfile,
    useLoggedIn,
    loading,
  }
  return <AuthContext.Provider value={value}>{!loading && children}</AuthContext.Provider>;

}


export function useAuth() {
  return useContext(AuthContext);
}